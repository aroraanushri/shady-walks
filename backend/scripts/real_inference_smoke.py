"""Run a real Mapillary download and local SegFormer inference.

Usage from backend:
    python scripts/real_inference_smoke.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image

from app.mapillary import MapillaryClient
from app.segmentation import (
    SegFormerSegmenter,
    calculate_gvi,
    render_mask,
    render_overlay,
)

ROOT = Path(__file__).parents[1]
load_dotenv(ROOT / ".env")


def main() -> None:
    client = MapillaryClient(
        __import__("os").getenv("MAPILLARY_TOKEN"),
        ROOT / "cache" / "mapillary",
    )
    images = client.search((73.819, 18.507, 73.825, 18.513), limit=10, minimum_distance_m=1)
    image = next((item for item in images if item.thumb_1024_url), None)
    if image is None:
        raise RuntimeError("Mapillary returned no image with a downloadable thumbnail in the bbox.")
    response = httpx.get(image.thumb_1024_url, timeout=30)
    response.raise_for_status()
    source = Image.open(__import__("io").BytesIO(response.content)).convert("RGB")
    segmenter = SegFormerSegmenter()
    started = time.perf_counter()
    result = segmenter.predict(source)
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    vegetation, valid, gvi = calculate_gvi(result.mask, result.vegetation_values)
    output = ROOT / ".local-results"
    output.mkdir(exist_ok=True)
    render_mask(result.mask, result.vegetation_values).save(output / "mask.png")
    render_overlay(source, result.mask, result.vegetation_values).save(output / "overlay.png")
    (output / "result.json").write_text(
        json.dumps(
            {
                "image_id": image.id,
                "source_attribution": image.attribution,
                "captured_at": image.captured_at,
                "source_dimensions": [source.width, source.height],
                "mask_dimensions": [int(result.mask.shape[1]), int(result.mask.shape[0])],
                "vegetation_labels": result.labels,
                "vegetation_pixels": vegetation,
                "valid_pixels": valid,
                "gvi_percent": gvi,
                "device": result.device,
                "latency_ms": latency_ms,
                "model": result.model,
                "license_note": (
                    "SegFormer model card links the NVlabs SegFormer license; verify "
                    "attribution before redistribution."
                ),
            },
            indent=2,
        )
    )
    print(json.dumps(json.loads((output / "result.json").read_text()), indent=2))
    print(f"Artifacts: {output / 'mask.png'}, {output / 'overlay.png'}")


if __name__ == "__main__":
    main()
