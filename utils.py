"""
utils.py — FaceShape AI
========================
Model loading, preprocessing, inference, and Grad-CAM.

Architecture: EfficientNet-B0 fine-tuned on 5-class face shape dataset.
Classes: Heart | Oblong | Oval | Round | Square
"""

from __future__ import annotations
import numpy as np
from pathlib import Path
from typing import List, Dict

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import matplotlib
matplotlib.use("Agg")          # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# ─────────────────────────────────────────────────────────────────────────────
CLASS_NAMES: List[str] = ["Heart", "Oblong", "Oval", "Round", "Square"]
IMG_SIZE    = 224
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Normalisation used during training
_MEAN = [0.485, 0.456, 0.406]
_STD  = [0.229, 0.224, 0.225]

_INFER_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=_MEAN, std=_STD),
])


# ═════════════════════════════════════════════════════════════════════════════
# MODEL
# ═════════════════════════════════════════════════════════════════════════════
def load_model(weights_path: str) -> nn.Module:
    """
    Rebuild EfficientNet-B0 with 5-class head and load saved weights.
    Falls back to random weights if .pth not found (useful for first-run tests).
    """
    model = models.efficientnet_b0(weights=None)
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, len(CLASS_NAMES))

    p = Path(weights_path)
    if p.exists():
        state = torch.load(weights_path, map_location=DEVICE)
        model.load_state_dict(state)
        print(f"[utils] Loaded weights from {weights_path}")
    else:
        print(f"[utils] WARNING: {weights_path} not found — using random weights!")

    model.to(DEVICE)
    model.eval()
    return model


# ═════════════════════════════════════════════════════════════════════════════
# INFERENCE
# ═════════════════════════════════════════════════════════════════════════════
def predict(model: nn.Module, image_path: str) -> List[Dict]:
    """
    Run inference on a single image.

    Returns:
        List of dicts sorted by confidence desc:
        [{"label": "Heart", "confidence": 0.884}, ...]
    """
    img    = _load_pil(image_path)
    tensor = _INFER_TF(img).unsqueeze(0).to(DEVICE)   # (1, 3, 224, 224)

    with torch.no_grad():
        logits = model(tensor)                          # (1, 5)
        probs  = torch.softmax(logits, dim=1)[0]        # (5,)

    results = [
        {"label": CLASS_NAMES[i], "confidence": round(float(probs[i]), 4)}
        for i in range(len(CLASS_NAMES))
    ]
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# GRAD-CAM
# ═════════════════════════════════════════════════════════════════════════════
class _GradCAM:
    """
    Grad-CAM implementation for EfficientNet-B0.
    Hooks on model.features[-1] (the last Conv2dNormActivation block).
    """

    def __init__(self, model: nn.Module):
        self.model       = model
        self.activations = None
        self.gradients   = None
        self._hooks: list = []

        target = model.features[-1]   # Conv2dNormActivation (1280-ch output)
        self._hooks.append(
            target.register_forward_hook(self._save_activations)
        )
        self._hooks.append(
            target.register_full_backward_hook(self._save_gradients)
        )

    def _save_activations(self, _, __, output):
        self.activations = output.detach()

    def _save_gradients(self, _, __, grad_output):
        self.gradients = grad_output[0].detach()

    def remove(self):
        for h in self._hooks:
            h.remove()

    def __call__(self, tensor: torch.Tensor, class_idx: int) -> np.ndarray:
        """
        Args:
            tensor:    preprocessed image (1, 3, 224, 224)
            class_idx: target class index
        Returns:
            Normalised CAM as np.ndarray float32 in [0, 1], shape (H, W)
        """
        self.model.zero_grad()
        logits = self.model(tensor)          # (1, 5)
        score  = logits[0, class_idx]
        score.backward()

        # Global average pooling of gradients → channel weights
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        cam     = (weights * self.activations).sum(dim=1)[0]      # (H, W)
        cam     = torch.relu(cam).cpu().numpy()

        # Normalise to [0, 1]
        if cam.max() > 0:
            cam = cam / cam.max()
        return cam.astype(np.float32)


def generate_gradcam(
    model: nn.Module,
    image_path: str,
    target_class_idx: int,
    output_path: str,
    alpha: float = 0.5,
) -> None:
    """
    Generate a Grad-CAM overlay PNG and save to output_path.

    Args:
        model:            loaded EfficientNet-B0
        image_path:       path to the input image
        target_class_idx: class index to visualise (0–4)
        output_path:      where to save the result PNG
        alpha:            heatmap overlay transparency
    """
    orig  = _load_pil(image_path).resize((IMG_SIZE, IMG_SIZE))
    tensor = _INFER_TF(orig).unsqueeze(0).to(DEVICE)

    gcam = _GradCAM(model)
    cam  = gcam(tensor, target_class_idx)
    gcam.remove()

    # Resize CAM to image size
    cam_img = Image.fromarray(np.uint8(cam * 255)).resize(
        (IMG_SIZE, IMG_SIZE), Image.BILINEAR
    )
    cam_np  = np.array(cam_img) / 255.0

    # Apply colour map (jet) and blend
    heatmap  = cm.jet(cam_np)[:, :, :3]              # (H, W, 3) RGB float
    orig_np  = np.array(orig).astype(np.float32) / 255.0
    blended  = (1 - alpha) * orig_np + alpha * heatmap
    blended  = np.clip(blended, 0, 1)

    # Save
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), dpi=100)
    fig.patch.set_facecolor("#0f1724")

    titles = ["Original", "Grad-CAM Heatmap", "Overlay"]
    imgs   = [orig_np, heatmap, blended]
    for ax, img, title in zip(axes, imgs, titles):
        ax.imshow(img)
        ax.set_title(title, color="white", fontsize=11, pad=8)
        ax.axis("off")

    plt.suptitle(
        f"Grad-CAM — {CLASS_NAMES[target_class_idx]}",
        color="white", fontsize=13, fontweight="bold", y=1.02
    )
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight",
                facecolor="#0f1724", edgecolor="none")
    plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def _load_pil(path: str) -> Image.Image:
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img