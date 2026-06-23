# FaceForm AI — Face Shape Classifier

A production-ready web service for classifying face shapes using **EfficientNet-B0** and **PyTorch**, deployed as a Dockerized Flask API with a modern AI-SaaS frontend.

---

## Architecture

```
nginx (port 80)  →  gunicorn/flask (port 5000)  →  PyTorch EfficientNet-B0
                                                     ↑
                                                 Redis (rate limiting)
```

---

## Quick Start — Local Development

### 1. Clone & set up environment

```bash
git clone https://github.com/yourname/face-shape-classifier.git
cd face-shape-classifier

# Copy env template and edit values
cp .env.example .env

# Create virtualenv
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# or: .venv\Scripts\activate.bat  # Windows

# Install dependencies (CPU-only torch is faster for dev)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 2. Place your model file

```bash
# Copy your trained model to the project root
cp /path/to/your/face_shape_model.pth .
```

> The model must be an `EfficientNet-B0` `state_dict` with 5 output classes:
> `Heart`, `Oblong`, `Oval`, `Round`, `Square`.

### 3. Generate an API key

```bash
python manage.py create_api_key
# Paste the key into .env → API_KEY_LIST=your-generated-key
```

### 4. Run development server

```bash
python manage.py serve
# or: flask run --port 5000
```

Open http://localhost:5000 in your browser.

---

## Docker Deployment

### Prerequisites
- Docker ≥ 24.0
- Docker Compose ≥ 2.20

### Steps

```bash
# 1. Create model directory and place model
mkdir -p model
cp /path/to/face_shape_model.pth model/

# 2. Set your API key in .env
echo "API_KEY_LIST=your-secret-key-here" > .env

# 3. Build and start all services
docker-compose up --build

# Services started:
#   → nginx on http://localhost:80
#   → flask/gunicorn on internal port 5000
#   → redis on internal port 6379
```

### Stop services
```bash
docker-compose down
docker-compose down -v   # also remove volumes
```

---

## API Reference

### Authentication

All `/api/predict` requests require the `X-API-KEY` header:
```
X-API-KEY: your-api-key
```

### Endpoints

#### `GET /api/health`
Returns service health status. No auth required.

```json
{
  "status": "ok",
  "model_loaded": true,
  "uptime_seconds": 142.3,
  "device": "cpu",
  "version": "1.0.0"
}
```

#### `GET /api/classes`
Returns supported face shape classes. No auth required.

```json
{
  "status": "ok",
  "classes": ["Heart", "Oblong", "Oval", "Round", "Square"],
  "count": 5
}
```

#### `POST /api/predict`
Classify a face shape from an uploaded image.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Header: `X-API-KEY: <your-key>`
- Body field: `image` (JPG or PNG, max 8MB)

**Success Response (`200`):**
```json
{
  "status": "ok",
  "prediction": "Oval",
  "confidence": 0.872,
  "probs": {
    "Heart": 0.01,
    "Oblong": 0.03,
    "Oval": 0.872,
    "Round": 0.04,
    "Square": 0.03
  },
  "processing_time_ms": 123,
  "request_id": "a1b2c3d4"
}
```

**Error Response (`4xx/5xx`):**
```json
{
  "status": "error",
  "message": "Invalid file type. Allowed: jpg, jpeg, png"
}
```

#### `GET /api/metrics`
Prometheus-format metrics (protect behind firewall in production).

---

## Example curl Requests

```bash
# Health check
curl http://localhost/api/health

# List classes
curl http://localhost/api/classes

# Predict face shape
curl -X POST http://localhost/api/predict \
  -H "X-API-KEY: your-api-key" \
  -F "image=@/path/to/face.jpg"

# With HTTPS (production)
curl -X POST https://yourdomain.com/api/predict \
  -H "X-API-KEY: your-api-key" \
  -F "image=@face.jpg"
```

---

## Management CLI

```bash
# Validate that the model file loads correctly
python manage.py check_model

# Run a test inference (uses random noise if no image given)
python manage.py test_inference
python manage.py test_inference --image face.jpg

# Generate a new API key
python manage.py create_api_key

# Start development server
python manage.py serve --port 5000
```

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Single test file
pytest tests/test_api.py -v
```

---

## Code Quality

```bash
# Format code
black .
isort .

# Lint
flake8 .

# Run everything
black . && isort . && flake8 . && pytest tests/
```

---

## Production Checklist

- [ ] Replace `API_KEY_LIST=dev-key-change-me` with a real secret key
- [ ] Set `FLASK_ENV=production`
- [ ] Configure SSL in `nginx.conf` (uncomment HTTPS server block)
- [ ] Store model file in a volume or object storage (not in Git)
- [ ] Set `REDIS_URL` for distributed rate limiting across workers
- [ ] Configure log shipping (e.g., to Datadog, CloudWatch)
- [ ] Set resource limits in `docker-compose.yml` (`mem_limit`, `cpus`)
- [ ] Add Prometheus/Grafana dashboard for `/api/metrics`
- [ ] Set up alerting for `/api/health` failures

---

## Gunicorn Production Command

```bash
# Manually (without docker)
gunicorn -w 4 -k gthread --threads 2 --timeout 120 \
  --bind 0.0.0.0:5000 \
  --access-logfile - \
  --error-logfile - \
  app:app

# Using config file
gunicorn --config gunicorn.conf.py app:app
```

---

## Environment Variables Reference

| Variable              | Default                  | Description                              |
|-----------------------|--------------------------|------------------------------------------|
| `API_KEY_LIST`        | `dev-key-change-me`      | Comma-separated API keys (**change this**)|
| `MODEL_PATH`          | `face_shape_model.pth`   | Path to trained PyTorch model            |
| `FLASK_ENV`           | `production`             | `development` or `production`            |
| `MAX_CONTENT_LENGTH`  | `8388608`                | Max upload size in bytes (8MB)           |
| `RATE_LIMIT`          | `60 per minute`          | Per-IP rate limit                        |
| `WORKERS`             | `4`                      | Gunicorn worker count                    |
| `THREADS`             | `2`                      | Threads per Gunicorn worker              |
| `TIMEOUT`             | `120`                    | Gunicorn worker timeout (seconds)        |
| `REDIS_URL`           | `memory://`              | Redis URL for distributed rate limiting  |
| `PORT`                | `5000`                   | Flask/Gunicorn bind port                 |
| `LOG_LEVEL`           | `info`                   | Logging level                            |

---

## Model Details

| Property       | Value                    |
|---------------|--------------------------|
| Architecture  | EfficientNet-B0          |
| Parameters    | ~5.3M                    |
| Input size    | 224 × 224 px             |
| Classes       | 5 (Heart, Oblong, Oval, Round, Square) |
| Val Accuracy  | 83.5% (on test set)      |
| Framework     | PyTorch 2.x              |

---

## License

MIT — see LICENSE file.

---

*Powered by **EfficientNet-B0** + **PyTorch***
