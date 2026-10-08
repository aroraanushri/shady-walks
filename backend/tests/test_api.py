from io import BytesIO
from unittest.mock import Mock

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.main import MAX_IMAGE_PIXELS, app, segmenter
from app.segmentation import SegmentationResult


def test_health_endpoint() -> None:
    assert TestClient(app).get("/health").json()["status"] == "ok"


def test_analyze_rejects_non_image() -> None:
    response = TestClient(app).post(
        "/api/analyze", files={"image": ("notes.txt", b"not an image", "text/plain")}
    )

    assert response.status_code == 415


def test_analyze_uses_mocked_segmenter() -> None:
    source = Image.new("RGB", (2, 2), (20, 80, 30))
    buffer = BytesIO()
    source.save(buffer, format="PNG")
    original = segmenter.predict
    segmenter.predict = Mock(
        return_value=SegmentationResult(np.array([[1, 0], [1, 0]]), ["tree"], {1}, "cpu")
    )
    try:
        response = TestClient(app).post(
            "/api/analyze",
            files={"image": ("sample.png", buffer.getvalue(), "image/png")},
        )
    finally:
        segmenter.predict = original

    assert response.status_code == 200
    assert response.json()["gvi_percent"] == 50.0
    assert response.json()["observed_only"] is True


def test_analyze_rejects_malformed_image() -> None:
    response = TestClient(app).post(
        "/api/analyze", files={"image": ("sample.png", b"not an image", "image/png")}
    )

    assert response.status_code == 400


def test_analyze_rejects_excessive_decoded_pixels(monkeypatch) -> None:
    monkeypatch.setattr("app.main.MAX_IMAGE_PIXELS", 1)
    source = Image.new("RGB", (2, 2), (20, 80, 30))
    buffer = BytesIO()
    source.save(buffer, format="PNG")

    response = TestClient(app).post(
        "/api/analyze",
        files={"image": ("sample.png", buffer.getvalue(), "image/png")},
    )

    assert response.status_code == 413
    assert MAX_IMAGE_PIXELS == 20_000_000
