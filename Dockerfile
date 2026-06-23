# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder — install Python deps in a venv
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed by some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for Docker layer cache
COPY requirements.txt .

# Install CPU-only torch (much smaller image; swap URL for CUDA variant if needed)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime — lean production image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="you@example.com"
LABEL description="Face Shape Classifier — production Flask service"

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY app.py model_utils.py manage.py gunicorn.conf.py ./
COPY templates/ ./templates/
COPY static/ ./static/

# Model file should be mounted via volume or copied here at build time.
# To embed model in image (not recommended for large files):
#   COPY face_shape_model.pth .
# For volume mount, set MODEL_PATH env var in docker-compose.yml.

# Create directory for logs
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

USER appuser

# ── Environment defaults (override in docker-compose.yml) ────────────────────
ENV FLASK_ENV=production \
    MODEL_PATH=/app/face_shape_model.pth \
    PORT=5000 \
    WORKERS=4 \
    THREADS=2 \
    TIMEOUT=120

EXPOSE 5000

# Health check — Docker will restart container if unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Start Gunicorn — config loaded from gunicorn.conf.py
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
