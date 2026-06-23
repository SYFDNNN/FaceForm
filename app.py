"""
Face Shape Classifier — Flask REST API
Production-ready with auth, rate limiting, logging, and metrics.
"""

import time
import logging
import os
import uuid
from functools import wraps
from threading import Lock

from flask import Flask, request, jsonify, render_template, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

from model_utils import FaceShapeModel, preprocess_image, CLASSES
from recommendations import get_recommendations

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("face_shape_api")

# ─── App Init ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Config from environment variables (set in docker-compose or .env)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 8 * 1024 * 1024))  # 8MB
app.config["MODEL_PATH"] = os.getenv("MODEL_PATH", "face_shape_model.pth")
app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "production")

# API key list: comma-separated in env var API_KEY_LIST
# Example: API_KEY_LIST="key1,key2,key3"
_raw_keys = os.getenv("API_KEY_LIST", "dev-key-change-me")
API_KEYS: set[str] = {k.strip() for k in _raw_keys.split(",") if k.strip()}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
# Configurable via env var: RATE_LIMIT (default "60 per minute")
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[os.getenv("RATE_LIMIT", "60 per minute")],
    storage_uri=os.getenv("REDIS_URL", "memory://"),
)

# ─── Model Singleton ──────────────────────────────────────────────────────────
_model: FaceShapeModel | None = None
_model_lock = Lock()
_app_start_time = time.time()
_request_count = 0
_latency_total = 0.0


def get_model() -> FaceShapeModel:
    """Thread-safe lazy model loader."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # double-check inside lock
                logger.info("Loading model from %s …", app.config["MODEL_PATH"])
                _model = FaceShapeModel(app.config["MODEL_PATH"])
                logger.info("Model loaded successfully on device: %s", _model.device)
    return _model


# Pre-load model at startup so first request isn't slow
with app.app_context():
    try:
        get_model()
    except Exception as exc:
        logger.warning("Could not pre-load model at startup: %s", exc)


# ─── Auth Decorator ───────────────────────────────────────────────────────────
def require_api_key(f):
    """Validate X-API-KEY header for protected endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-KEY", "")
        if key not in API_KEYS:
            logger.warning("Unauthorized request from %s", request.remote_addr)
            return jsonify({"status": "error", "message": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Request Hooks ────────────────────────────────────────────────────────────
@app.before_request
def before_request():
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())[:8]


@app.after_request
def after_request(response):
    global _request_count, _latency_total
    elapsed_ms = (time.time() - g.get("start_time", time.time())) * 1000
    _request_count += 1
    _latency_total += elapsed_ms
    response.headers["X-Request-ID"] = g.get("request_id", "")
    response.headers["X-Processing-Time-Ms"] = f"{elapsed_ms:.1f}"
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ─── Helpers ──────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the SPA frontend."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Service health check — public endpoint."""
    model_loaded = False
    try:
        m = get_model()
        model_loaded = m is not None
    except Exception:
        pass

    return jsonify({
        "status": "ok",
        "model_loaded": model_loaded,
        "uptime_seconds": round(time.time() - _app_start_time, 1),
        "device": str(_model.device) if _model else "unknown",
        "version": "1.0.0",
    })


@app.route("/api/classes", methods=["GET"])
def classes():
    """Return list of supported face shape classes — public endpoint."""
    return jsonify({
        "status": "ok",
        "classes": CLASSES,
        "count": len(CLASSES),
    })


@app.route("/api/metrics", methods=["GET"])
def metrics():
    """Prometheus-style metrics endpoint. Protect in production with firewall."""
    avg_latency = (_latency_total / _request_count) if _request_count > 0 else 0.0
    # Plain-text Prometheus format
    lines = [
        "# HELP face_shape_requests_total Total number of HTTP requests",
        "# TYPE face_shape_requests_total counter",
        f"face_shape_requests_total {_request_count}",
        "# HELP face_shape_avg_latency_ms Average request latency in milliseconds",
        "# TYPE face_shape_avg_latency_ms gauge",
        f"face_shape_avg_latency_ms {avg_latency:.2f}",
        "# HELP face_shape_uptime_seconds App uptime in seconds",
        "# TYPE face_shape_uptime_seconds gauge",
        f"face_shape_uptime_seconds {time.time() - _app_start_time:.1f}",
    ]
    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; version=0.0.4"}


@app.route("/api/predict", methods=["POST"])
@require_api_key
@limiter.limit("30 per minute")
def predict():
    """
    POST /api/predict
    Headers: X-API-KEY: <your-key>
    Body: multipart/form-data — fields: 'image' (file), 'gender' (male|female)
    Returns: JSON with prediction, confidence, probabilities, and recommendations.
    """
    global _request_count

    t_start = time.time()

    # ── Validate gender ───────────────────────────────────────────────────────
    gender = request.form.get("gender", "").strip().lower()
    if gender not in ("male", "female"):
        return jsonify({
            "status": "error",
            "message": "Gender is required. Must be 'male' or 'female'.",
        }), 400

    # ── Validate file presence ────────────────────────────────────────────────
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image field in request"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        }), 415

    # ── Read & preprocess ─────────────────────────────────────────────────────
    try:
        img_bytes = file.read()
        if len(img_bytes) == 0:
            return jsonify({"status": "error", "message": "Empty file"}), 400

        tensor = preprocess_image(img_bytes)
    except Exception as exc:
        logger.error("Preprocessing error: %s", exc)
        return jsonify({"status": "error", "message": "Failed to process image. Ensure it is a valid image."}), 422

    # ── Inference ─────────────────────────────────────────────────────────────
    try:
        model = get_model()
        prediction, confidence, probs = model.predict(tensor)
    except FileNotFoundError as exc:
        logger.error("Model file not found: %s", exc)
        dev = app.config["FLASK_ENV"] == "development"
        msg = str(exc) if dev else "Model file not found. Check MODEL_PATH."
        return jsonify({"status": "error", "message": msg}), 500
    except Exception as exc:
        logger.error("Inference error [%s]: %s", type(exc).__name__, exc, exc_info=True)
        dev = app.config["FLASK_ENV"] == "development"
        msg = f"{type(exc).__name__}: {exc}" if dev else "Model inference failed"
        return jsonify({"status": "error", "message": msg}), 500

    # ── Recommendations ───────────────────────────────────────────────────────
    try:
        recommendations = get_recommendations(gender, prediction)
    except Exception as exc:
        logger.warning("Recommendations error: %s", exc)
        recommendations = {}

    processing_time_ms = round((time.time() - t_start) * 1000, 1)

    # ── Logging ───────────────────────────────────────────────────────────────
    logger.info(
        "predict | req_id=%s | ip=%s | gender=%s | prediction=%s | confidence=%.3f | time_ms=%.1f",
        g.request_id,
        request.remote_addr,
        gender,
        prediction,
        confidence,
        processing_time_ms,
    )

    return jsonify({
        "status": "ok",
        "gender": gender,
        "prediction": prediction,
        "confidence": round(float(confidence), 4),
        "probs": {cls: round(float(p), 4) for cls, p in probs.items()},
        "recommendations": recommendations,
        "processing_time_ms": processing_time_ms,
        "request_id": g.request_id,
    })


# ─── Error Handlers ───────────────────────────────────────────────────────────
@app.errorhandler(413)
def request_entity_too_large(error):
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return jsonify({"status": "error", "message": f"File too large. Max size: {max_mb}MB"}), 413


@app.errorhandler(429)
def too_many_requests(error):
    return jsonify({"status": "error", "message": "Rate limit exceeded. Please slow down."}), 429


@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Development only — use Gunicorn in production
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=(app.config["FLASK_ENV"] == "development"),
    )
