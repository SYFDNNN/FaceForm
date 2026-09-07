# Model artifacts

Place the trained EfficientNet-B0 state dict here as:

```text
models/face_shape_model.pth
```

Model binaries are ignored by Git. For deployment, mount the model through the `model_data` volume or set `MODEL_PATH` to a securely hosted artifact.
