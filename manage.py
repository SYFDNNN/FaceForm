#!/usr/bin/env python3
"""
manage.py — CLI management helper for Face Shape Classifier.

Commands:
    python manage.py reload_model     Hot-reload the model (requires running server)
    python manage.py test_inference   Run a local inference test on a sample image
    python manage.py check_model      Validate model file and architecture
    python manage.py serve            Start development server
    python manage.py create_api_key   Generate a random API key
"""

import argparse
import io
import logging
import os
import secrets
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("manage")


# ─── Commands ─────────────────────────────────────────────────────────────────
def cmd_check_model(args):
    """Validate model file exists and can be loaded."""
    model_path = args.model_path or os.getenv("MODEL_PATH", "models/face_shape_model.pth")
    logger.info("Checking model: %s", model_path)

    try:
        from src.faceshape.model import FaceShapeModel

        model = FaceShapeModel(model_path)
        logger.info("✅ Model loaded successfully on device: %s", model.device)
    except FileNotFoundError as exc:
        logger.error("❌ Model file not found: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("❌ Model load failed: %s", exc)
        sys.exit(1)


def cmd_test_inference(args):
    """Run a test inference using a synthetic or supplied image."""
    model_path = args.model_path or os.getenv("MODEL_PATH", "models/face_shape_model.pth")

    try:
        import numpy as np
        from PIL import Image

        from src.faceshape.model import FaceShapeModel, preprocess_image
    except ImportError as exc:
        logger.error("Missing dependency: %s", exc)
        sys.exit(1)

    logger.info("Loading model from %s …", model_path)
    model = FaceShapeModel(model_path)

    if args.image:
        logger.info("Loading image: %s", args.image)
        with open(args.image, "rb") as f:
            img_bytes = f.read()
    else:
        # Generate a random 224×224 RGB image as a smoke test
        logger.info("No image supplied — using random noise image for smoke test")
        arr = (np.random.rand(224, 224, 3) * 255).astype("uint8")
        img = Image.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()

    t0 = time.time()
    tensor = preprocess_image(img_bytes)
    prediction, confidence, probs = model.predict(tensor)
    elapsed_ms = (time.time() - t0) * 1000

    print("\n" + "─" * 40)
    print(f"  Prediction  : {prediction}")
    print(f"  Confidence  : {confidence:.1%}")
    print(f"  Time        : {elapsed_ms:.1f} ms")
    print("  Probabilities:")
    for cls, p in sorted(probs.items(), key=lambda x: -x[1]):
        bar = "█" * int(p * 20)
        print(f"    {cls:<10} {p:.3f}  {bar}")
    print("─" * 40 + "\n")


def cmd_create_api_key(args):
    """Generate a cryptographically secure API key."""
    key = secrets.token_urlsafe(32)
    print(f"\n  Generated API key:\n\n    {key}\n")
    print("  Add to your environment:\n")
    print(f"    export API_KEY_LIST={key}\n")
    print("  Or in docker-compose.yml:\n")
    print(f"    API_KEY_LIST: {key}\n")


def cmd_serve(args):
    """Start the development Flask server."""
    os.environ.setdefault("FLASK_ENV", "development")
    os.environ.setdefault("MODEL_PATH", "models/face_shape_model.pth")
    from app import app

    app.run(host="0.0.0.0", port=int(args.port), debug=True)


def cmd_reload_model(args):
    """
    Signal a running server to reload its model.
    Requires the server to be accessible at --url.
    """
    import urllib.error
    import urllib.request

    url = f"{args.url.rstrip('/')}/api/health"
    try:
        req = urllib.request.urlopen(url, timeout=5)
        import json

        data = json.loads(req.read())
        logger.info(
            "Server status: %s | model_loaded: %s", data.get("status"), data.get("model_loaded")
        )
    except urllib.error.URLError as exc:
        logger.error("Cannot reach server at %s: %s", url, exc)
        sys.exit(1)

    # In production you'd call a protected /api/admin/reload endpoint.
    # For now, the recommended approach is to restart the gunicorn worker.
    logger.info("To hot-reload in production, send SIGHUP to gunicorn master:")
    logger.info("  kill -HUP $(cat gunicorn.pid)")


# ─── CLI Parser ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Face Shape Classifier management CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check_model
    p_check = subparsers.add_parser("check_model", help="Validate model file")
    p_check.add_argument("--model-path", default=None, help="Path to .pth file")
    p_check.set_defaults(func=cmd_check_model)

    # test_inference
    p_test = subparsers.add_parser("test_inference", help="Run local inference test")
    p_test.add_argument("--model-path", default=None, help="Path to .pth file")
    p_test.add_argument("--image", default=None, help="Path to image file (optional)")
    p_test.set_defaults(func=cmd_test_inference)

    # create_api_key
    p_key = subparsers.add_parser("create_api_key", help="Generate a new API key")
    p_key.set_defaults(func=cmd_create_api_key)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start development server")
    p_serve.add_argument("--port", default="5000", help="Port (default: 5000)")
    p_serve.set_defaults(func=cmd_serve)

    # reload_model
    p_reload = subparsers.add_parser("reload_model", help="Reload model on running server")
    p_reload.add_argument("--url", default="http://localhost:5000", help="Server URL")
    p_reload.set_defaults(func=cmd_reload_model)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
