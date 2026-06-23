"""
tests/test_model_utils.py — Unit tests for model_utils.py.

Run with: pytest tests/ -v
"""

import io
from unittest.mock import MagicMock, patch

import pytest
import torch
from PIL import Image

from model_utils import CLASSES, NUM_CLASSES, preprocess_image, build_model


# ─── preprocess_image ─────────────────────────────────────────────────────────
class TestPreprocessImage:
    def _make_jpeg(self, size=(224, 224), mode="RGB") -> bytes:
        img = Image.new(mode, size, color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def _make_png(self, size=(100, 80), mode="RGBA") -> bytes:
        img = Image.new(mode, size)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_returns_tensor(self):
        tensor = preprocess_image(self._make_jpeg())
        assert isinstance(tensor, torch.Tensor)

    def test_output_shape(self):
        tensor = preprocess_image(self._make_jpeg())
        assert tensor.shape == (1, 3, 224, 224)

    def test_small_image_resized(self):
        tensor = preprocess_image(self._make_jpeg(size=(50, 50)))
        assert tensor.shape == (1, 3, 224, 224)

    def test_large_image_resized(self):
        tensor = preprocess_image(self._make_jpeg(size=(1024, 768)))
        assert tensor.shape == (1, 3, 224, 224)

    def test_rgba_image_converted(self):
        """RGBA (PNG with transparency) must be converted to RGB."""
        tensor = preprocess_image(self._make_png(mode="RGBA"))
        assert tensor.shape == (1, 3, 224, 224)

    def test_grayscale_converted(self):
        img = Image.new("L", (224, 224), 128)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        tensor = preprocess_image(buf.getvalue())
        assert tensor.shape == (1, 3, 224, 224)

    def test_invalid_bytes_raises_valueerror(self):
        with pytest.raises(ValueError):
            preprocess_image(b"this is not an image")

    def test_normalization_applied(self):
        """Output should be normalized (not in [0, 255])."""
        tensor = preprocess_image(self._make_jpeg())
        # After ImageNet normalization, values are typically in [-3, 3]
        assert tensor.min().item() < 1.0
        assert tensor.max().item() < 5.0


# ─── build_model ──────────────────────────────────────────────────────────────
class TestBuildModel:
    def test_output_classes(self):
        import torch.nn as nn
        model = build_model(num_classes=5)
        assert isinstance(model.classifier[1], nn.Linear)
        assert model.classifier[1].out_features == 5

    def test_forward_pass_shape(self):
        model = build_model(num_classes=5)
        model.eval()
        dummy = torch.zeros(1, 3, 224, 224)
        with torch.no_grad():
            out = model(dummy)
        assert out.shape == (1, 5)


# ─── CLASSES constant ─────────────────────────────────────────────────────────
class TestConstants:
    def test_classes_count(self):
        assert len(CLASSES) == NUM_CLASSES == 5

    def test_classes_names(self):
        assert set(CLASSES) == {"Heart", "Oblong", "Oval", "Round", "Square"}
