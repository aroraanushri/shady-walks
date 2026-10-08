from __future__ import annotations

import base64
import io
import re
from dataclasses import dataclass

import numpy as np
from PIL import Image

MODEL_CHECKPOINT = "nvidia/segformer-b0-finetuned-ade-512-512"
VEGETATION_LABELS = {"tree", "grass", "plant", "flower", "palm", "bush", "shrub"}


def is_vegetation_label(label: str) -> bool:
    words = set(re.findall(r"[a-z]+", label.lower()))
    return bool(words & VEGETATION_LABELS)


@dataclass(frozen=True)
class SegmentationResult:
    mask: np.ndarray
    labels: list[str]
    vegetation_values: set[int]
    device: str
    model: str = MODEL_CHECKPOINT


def calculate_gvi(mask: np.ndarray, vegetation_values: set[int]) -> tuple[int, int, float]:
    """Return vegetation pixels, valid pixels, and visible vegetation percentage."""
    valid = mask >= 0
    valid_pixels = int(np.count_nonzero(valid))
    vegetation_pixels = int(np.count_nonzero(np.isin(mask, list(vegetation_values)) & valid))
    gvi = (vegetation_pixels / valid_pixels * 100) if valid_pixels else 0.0
    return vegetation_pixels, valid_pixels, round(gvi, 2)


def encode_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class SegFormerSegmenter:
    """Lazy local SegFormer wrapper. Construction never downloads model weights."""

    def __init__(self, checkpoint: str = MODEL_CHECKPOINT) -> None:
        self.checkpoint = checkpoint
        self._processor = None
        self._model = None
        self._device = None

    def _load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._processor = SegformerImageProcessor.from_pretrained(self.checkpoint)
        self._model = SegformerForSemanticSegmentation.from_pretrained(self.checkpoint).to(
            self._device
        )
        self._model.eval()

    def predict(self, image: Image.Image) -> SegmentationResult:
        self._load()
        import torch

        assert self._processor is not None and self._model is not None and self._device is not None
        inputs = self._processor(images=image, return_tensors="pt").to(self._device)
        with torch.inference_mode():
            logits = self._model(**inputs).logits
        mask = logits.argmax(dim=1)[0].detach().cpu().numpy().astype(np.int16)
        mask = np.asarray(
            Image.fromarray(mask.astype(np.int32), mode="I").resize(
                image.size, Image.Resampling.NEAREST
            ),
            dtype=np.int16,
        )
        id2label = self._model.config.id2label
        vegetation_values = {
            int(index)
            for index, label in id2label.items()
            if is_vegetation_label(str(label))
        }
        vegetation_labels = [
            str(label)
            for index, label in id2label.items()
            if is_vegetation_label(str(label))
            and int(index) in np.unique(mask)
        ]
        return SegmentationResult(
            mask, vegetation_labels, vegetation_values, str(self._device), self.checkpoint
        )


def render_mask(mask: np.ndarray, vegetation_values: set[int]) -> Image.Image:
    pixels = np.zeros((*mask.shape, 4), dtype=np.uint8)
    pixels[np.isin(mask, list(vegetation_values))] = (39, 174, 96, 220)
    pixels[mask < 0] = (120, 120, 120, 160)
    return Image.fromarray(pixels, mode="RGBA")


def render_overlay(
    image: Image.Image, mask: np.ndarray, vegetation_values: set[int]
) -> Image.Image:
    overlay = image.convert("RGBA").resize((mask.shape[1], mask.shape[0]))
    vegetation = render_mask(mask, vegetation_values)
    return Image.blend(overlay, vegetation, alpha=0.42)
