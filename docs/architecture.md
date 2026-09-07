# Architecture

FaceForm is split into a thin Flask entry point and a small application package:

```text
Browser ──▶ Nginx ──▶ Gunicorn ──▶ app.py ──▶ src/faceshape
                                      ├── model.py
                                      └── recommendations.py
```

`model.py` owns EfficientNet-B0 construction, weight loading, image preprocessing, and inference. `recommendations.py` maps the predicted shape and selected gender to the visual recommendation assets in `static/`.

The model is loaded lazily and guarded by a lock so multiple Gunicorn threads can safely share one model instance. Redis is used by Docker Compose as the rate-limit backend; local development falls back to in-memory storage.
