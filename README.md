# FaceForm AI

AI-powered face shape classification and style recommendation service. The application combines a Flask API, an EfficientNet-B0 model, and a responsive web interface.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?logo=flask&logoColor=white)
![CI](https://github.com/SYFDNNN/FaceForm/actions/workflows/ci.yml/badge.svg)

## Highlights

- EfficientNet-B0 inference with CPU/GPU detection and thread-safe model loading
- Five-class prediction: Heart, Oblong, Oval, Round, and Square
- Personalized hairstyle and glasses recommendations
- Protected prediction endpoint with API-key authentication and rate limiting
- Docker Compose setup with Gunicorn, Nginx, and Redis
- Automated formatting, linting, tests, and Docker build in GitHub Actions

## Project structure

```text
.
├── app.py                  # WSGI entry point
├── manage.py               # Local development and model CLI
├── src/faceshape/          # Application package
│   ├── model.py            # Model architecture, loading, preprocessing
│   └── recommendations.py  # Style recommendation rules
├── templates/              # Flask HTML templates
├── static/                 # CSS, JavaScript, and UI assets
├── tests/                  # API and model tests
├── scripts/                # Training/experimentation helpers
├── notebooks/              # Exploratory notebooks
├── data/                   # Dataset documentation and local raw data
├── models/                 # Local model weights (ignored by Git)
├── docs/                   # Technical documentation
├── Dockerfile
└── docker-compose.yml
```

Large datasets, model weights, databases, uploads, and secrets are intentionally excluded from version control. See [data/README.md](data/README.md) and [models/README.md](models/README.md).

## Quick start

```bash
git clone https://github.com/SYFDNNN/FaceForm.git
cd FaceForm
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
copy .env.example .env       # Windows; use cp on Linux/macOS
```

Place the trained weights at `models/face_shape_model.pth`, then run:

```bash
python manage.py serve
```

Open <http://localhost:5000>. For the complete production-like stack:

```bash
docker compose up --build
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/health` | Service and model status |
| `GET /api/classes` | Supported face shape classes |
| `POST /api/predict` | Predict a face shape and return recommendations |
| `GET /api/metrics` | Prometheus-style application metrics |

`POST /api/predict` expects `multipart/form-data` with `image` and `gender` (`male` or `female`) and requires the `X-API-KEY` header.

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "X-API-KEY: your-key" \
  -F "gender=female" \
  -F "image=@face.jpg"
```

## Development commands

```bash
python manage.py check_model
python manage.py test_inference --image face.jpg
pytest -q
black . && isort . && flake8 .
```

## Model

The inference pipeline uses EfficientNet-B0 with a 224×224 input and ImageNet normalization. The reported evaluation accuracy is 83.5% on the project test set; treat this as an experiment-specific result, not a guarantee for every image or demographic group.

## License

MIT. See [LICENSE](LICENSE).
