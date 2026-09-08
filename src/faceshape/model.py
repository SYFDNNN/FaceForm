"""
model_utils.py — Model loading, preprocessing, and inference utilities.

This module handles:
- EfficientNet-B0 model loading with CPU/GPU device detection
- Thread-safe inference wrapper
- Image preprocessing matching training pipeline
- Optional TorchScript (JIT) tracing for speedup
"""

import io
import logging
import threading
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

logger = logging.getLogger("face_shape_api.model_utils")

# ─── Constants ────────────────────────────────────────────────────────────────
CLASSES: list[str] = ["Heart", "Oblong", "Oval", "Round", "Square"]
NUM_CLASSES = len(CLASSES)
IMG_SIZE = 224

# ImageNet normalization stats used during training
_MEAN = [0.485, 0.456, 0.406]
_STD = [0.229, 0.224, 0.225]

# Preprocessing pipeline — must match training val_transform exactly
INFERENCE_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=_MEAN, std=_STD),
    ]
)


# ─── Model Builder ────────────────────────────────────────────────────────────
def build_model(num_classes: int = NUM_CLASSES) -> nn.Module:
    """
    Build EfficientNet-B0 architecture with a custom classifier head.
    Matches the training configuration exactly.
    """
    # Use weights=None here because we load our own fine-tuned weights below
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


# ─── FaceShapeModel Class ─────────────────────────────────────────────────────
class FaceShapeModel:
    """
    Thread-safe wrapper around the EfficientNet-B0 face shape classifier.

    Usage:
        model = FaceShapeModel("face_shape_model.pth")
        prediction, confidence, probs = model.predict(tensor)
    """

    def __init__(self, model_path: str, use_jit: bool = False) -> None:
        """
        Load model weights and prepare for inference.

        Args:
            model_path: Path to .pth file with model state_dict.
            use_jit: If True, trace model with TorchScript for potential speedup.
        """
        self._lock = threading.Lock()
        self.device = self._detect_device()
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}. "
                "Set MODEL_PATH env var or place the file in the project root."
            )

        self._model = self._load_model(use_jit=use_jit)
        logger.info("FaceShapeModel ready | device=%s | path=%s", self.device, model_path)

    # ── Private Helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _detect_device() -> torch.device:
        """Prefer GPU if available, fallback to CPU."""
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info("CUDA GPU detected: %s", torch.cuda.get_device_name(0))
        else:
            device = torch.device("cpu")
            logger.info("No GPU found, using CPU for inference")
        return device

    def _load_model(self, use_jit: bool) -> nn.Module:
        """Load weights into architecture and set eval mode."""
        net = build_model(NUM_CLASSES)

        # Load state dict; map to correct device.
        # weights_only=True is safer but may fail on models saved with older PyTorch.
        # We try safe mode first, then fall back.
        try:
            state = torch.load(
                self.model_path,
                map_location=self.device,
                weights_only=True,
            )
        except Exception:
            logger.warning(
                "weights_only=True failed — retrying with weights_only=False "
                "(safe for models you trained yourself)"
            )
            state = torch.load(
                self.model_path,
                map_location=self.device,
                weights_only=False,
            )

        # Support both raw state_dict and checkpoint dicts
        # e.g. torch.save({"model_state_dict": ..., "epoch": ...}, path)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        elif isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]

        net.load_state_dict(state)
        net.to(self.device)
        net.eval()

        if use_jit:
            # TorchScript trace can speed up CPU-only deployments
            dummy = torch.zeros(1, 3, IMG_SIZE, IMG_SIZE, device=self.device)
            net = torch.jit.trace(net, dummy)
            logger.info("Model traced with TorchScript")

        return net

    # ── Public API ────────────────────────────────────────────────────────────
    def predict(
        self,
        tensor: torch.Tensor,
    ) -> tuple[str, float, dict[str, float]]:
        """
        Run inference on a pre-processed image tensor.

        Args:
            tensor: Shape [1, 3, 224, 224], already normalized.

        Returns:
            Tuple of (predicted_class, confidence, {class: probability})
        """
        tensor = tensor.to(self.device)

        with self._lock:  # thread-safe: one inference at a time per model instance
            with torch.no_grad():
                logits = self._model(tensor)  # [1, NUM_CLASSES]
                probs = torch.softmax(logits, dim=1)  # [1, NUM_CLASSES]

        probs_list = probs.squeeze(0).cpu().tolist()  # [NUM_CLASSES]
        prob_dict = dict(zip(CLASSES, probs_list))

        predicted_idx = int(torch.argmax(probs, dim=1).item())
        predicted_class = CLASSES[predicted_idx]
        confidence = probs_list[predicted_idx]

        return predicted_class, confidence, prob_dict

    def reload(self) -> None:
        """Hot-reload model weights without restarting the server."""
        logger.info("Reloading model weights from %s", self.model_path)
        with self._lock:
            self._model = self._load_model(use_jit=False)
        logger.info("Model reload complete")


# ─── Image Preprocessing ──────────────────────────────────────────────────────
def preprocess_image(img_bytes: bytes) -> torch.Tensor:
    """
    Convert raw image bytes to a normalized tensor ready for inference.

    Args:
        img_bytes: Raw bytes of JPG/PNG image.

    Returns:
        Tensor of shape [1, 3, 224, 224].

    Raises:
        ValueError: If image cannot be decoded or is not RGB-convertible.
    """
    try:
        img = Image.open(io.BytesIO(img_bytes))
    except Exception as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc

    # Convert to RGB: handles RGBA, L (grayscale), palette modes
    if img.mode != "RGB":
        img = img.convert("RGB")

    tensor = INFERENCE_TRANSFORM(img)  # [3, 224, 224]
    return tensor.unsqueeze(0)  # [1, 3, 224, 224]
