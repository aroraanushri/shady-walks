from __future__ import annotations

import io
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from .mapillary import MapillaryClient, MapillaryError
from .schemas import AnalysisResponse
from .segmentation import (
    SegFormerSegmenter,
    calculate_gvi,
    encode_png,
    render_mask,
    render_overlay,
)

load_dotenv(Path(__file__).parents[1] / ".env")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
segmenter = SegFormerSegmenter()
app = FastAPI(title="ShadeShift API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
mapillary = MapillaryClient(
    os.getenv("MAPILLARY_TOKEN"),
    Path(__file__).parents[1] / "cache" / "mapillary",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shadeshift-api"}


@app.get("/api/mapillary/images")
def mapillary_images(
    west: float,
    south: float,
    east: float,
    north: float,
    limit: int = 10,
) -> dict[str, object]:
    try:
        images = mapillary.search((west, south, east, north), limit=limit)
    except MapillaryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"images": [image.__dict__ for image in images], "count": len(images)}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_image(image: UploadFile = File(...)) -> AnalysisResponse:  # noqa: B008
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")
    content = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        source = Image.open(io.BytesIO(content)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=400, detail="The uploaded file is not a readable image."
        ) from exc

    result = segmenter.predict(source)
    vegetation_values = result.vegetation_values
    vegetation_pixels, valid_pixels, gvi = calculate_gvi(result.mask, vegetation_values)
    return AnalysisResponse(
        filename=image.filename or "upload",
        width=source.width,
        height=source.height,
        vegetation_pixels=vegetation_pixels,
        valid_pixels=valid_pixels,
        gvi_percent=gvi,
        vegetation_labels=result.labels,
        device=result.device,
        model=result.model,
        mask_png_base64=encode_png(render_mask(result.mask, vegetation_values)),
        overlay_png_base64=encode_png(render_overlay(source, result.mask, vegetation_values)),
    )
