"""
tests/test_api.py — Integration tests for the Flask REST API.

Run with: pytest tests/ -v
"""

import io
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

# Set test environment variables BEFORE importing app
os.environ["MODEL_PATH"] = "fake_model.pth"
os.environ["API_KEY_LIST"] = "test-api-key"
os.environ["FLASK_ENV"] = "testing"


# ─── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def client():
    """Create a test Flask client with a mocked model."""
    mock_model = MagicMock()
    mock_model.device = "cpu"
    mock_model.predict.return_value = (
        "Oval",
        0.872,
        {"Heart": 0.01, "Oblong": 0.03, "Oval": 0.872, "Round": 0.04, "Square": 0.03},
    )

    with patch("app.get_model", return_value=mock_model), patch("app._model", mock_model):
        from app import app

        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client


@pytest.fixture
def valid_image_bytes():
    """Create a minimal valid JPEG image as bytes."""
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def valid_png_bytes():
    """Create a minimal valid PNG image as bytes."""
    img = Image.new("RGB", (100, 100), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ─── Health Endpoint ──────────────────────────────────────────────────────────
class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_json_structure(self, client):
        resp = client.get("/api/health")
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "uptime_seconds" in data
        assert "version" in data


# ─── Classes Endpoint ─────────────────────────────────────────────────────────
class TestClasses:
    def test_classes_returns_200(self, client):
        resp = client.get("/api/classes")
        assert resp.status_code == 200

    def test_classes_content(self, client):
        resp = client.get("/api/classes")
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "classes" in data
        assert set(data["classes"]) == {"Heart", "Oblong", "Oval", "Round", "Square"}
        assert data["count"] == 5


# ─── Predict Endpoint ─────────────────────────────────────────────────────────
class TestPredict:
    def test_predict_no_api_key_returns_401(self, client, valid_image_bytes):
        resp = client.post(
            "/api/predict",
            data={"image": (io.BytesIO(valid_image_bytes), "face.jpg")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 401

    def test_predict_wrong_api_key_returns_401(self, client, valid_image_bytes):
        resp = client.post(
            "/api/predict",
            headers={"X-API-KEY": "wrong-key"},
            data={"image": (io.BytesIO(valid_image_bytes), "face.jpg")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 401

    def test_predict_valid_jpeg_returns_200(self, client, valid_image_bytes):
        mock_model = MagicMock()
        mock_model.predict.return_value = (
            "Oval",
            0.872,
            {"Heart": 0.01, "Oblong": 0.03, "Oval": 0.872, "Round": 0.04, "Square": 0.03},
        )
        with patch("app.get_model", return_value=mock_model):
            resp = client.post(
                "/api/predict",
                headers={"X-API-KEY": "test-api-key"},
                data={"image": (io.BytesIO(valid_image_bytes), "face.jpg")},
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200

    def test_predict_response_structure(self, client, valid_image_bytes):
        mock_model = MagicMock()
        mock_model.predict.return_value = (
            "Oval",
            0.872,
            {"Heart": 0.01, "Oblong": 0.03, "Oval": 0.872, "Round": 0.04, "Square": 0.03},
        )
        with patch("app.get_model", return_value=mock_model):
            resp = client.post(
                "/api/predict",
                headers={"X-API-KEY": "test-api-key"},
                data={"image": (io.BytesIO(valid_image_bytes), "face.jpg")},
                content_type="multipart/form-data",
            )
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["prediction"] == "Oval"
        assert 0 <= data["confidence"] <= 1
        assert "probs" in data
        assert len(data["probs"]) == 5
        assert "processing_time_ms" in data

    def test_predict_valid_png_returns_200(self, client, valid_png_bytes):
        mock_model = MagicMock()
        mock_model.predict.return_value = (
            "Round",
            0.75,
            {"Heart": 0.02, "Oblong": 0.05, "Oval": 0.10, "Round": 0.75, "Square": 0.08},
        )
        with patch("app.get_model", return_value=mock_model):
            resp = client.post(
                "/api/predict",
                headers={"X-API-KEY": "test-api-key"},
                data={"image": (io.BytesIO(valid_png_bytes), "face.png")},
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200

    def test_predict_no_image_field_returns_400(self, client):
        resp = client.post(
            "/api/predict",
            headers={"X-API-KEY": "test-api-key"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "No image" in resp.get_json()["message"]

    def test_predict_invalid_extension_returns_415(self, client):
        resp = client.post(
            "/api/predict",
            headers={"X-API-KEY": "test-api-key"},
            data={"image": (io.BytesIO(b"fake"), "document.pdf")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 415

    def test_predict_empty_file_returns_400(self, client):
        resp = client.post(
            "/api/predict",
            headers={"X-API-KEY": "test-api-key"},
            data={"image": (io.BytesIO(b""), "face.jpg")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


# ─── Error Handlers ───────────────────────────────────────────────────────────
class TestErrors:
    def test_404_returns_json(self, client):
        resp = client.get("/this/does/not/exist")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["status"] == "error"
