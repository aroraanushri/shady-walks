from __future__ import annotations

import io
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
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
MAX_IMAGE_PIXELS = 20_000_000
MAPILLARY_IMAGE_TIMEOUT = 20
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


def decode_image(content: bytes) -> Image.Image:
    try:
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image has too many pixels.")
            image.verify()
        return Image.open(io.BytesIO(content)).convert("RGB")
    except Image.DecompressionBombError as exc:
        raise HTTPException(status_code=413, detail="Image has too many pixels.") from exc
    except (Image.DecompressionBombWarning, UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=400, detail="The uploaded file is not a readable image."
        ) from exc


def approved_mapillary_image_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and (
        host == "graph.mapillary.com" or host.endswith(".fbcdn.net")
    )


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
    source = decode_image(content)

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


@app.post("/api/analyze/mapillary/{image_id}", response_model=AnalysisResponse)
def analyze_mapillary_image(image_id: str) -> AnalysisResponse:
    try:
        metadata = mapillary.get_image(image_id)
    except MapillaryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not metadata.thumb_1024_url or not approved_mapillary_image_url(metadata.thumb_1024_url):
        raise HTTPException(status_code=502, detail="Mapillary returned an unapproved image URL.")
    try:
        with httpx.Client(timeout=MAPILLARY_IMAGE_TIMEOUT, follow_redirects=False) as client:
            response = client.get(metadata.thumb_1024_url)
            response.raise_for_status()
            content = response.content
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail="Mapillary thumbnail could not be retrieved."
        ) from exc
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Mapillary thumbnail is too large.")
    source = decode_image(content)
    result = segmenter.predict(source)
    vegetation_pixels, valid_pixels, gvi = calculate_gvi(
        result.mask, result.vegetation_values
    )
    return AnalysisResponse(
        filename=f"mapillary-{metadata.id}.jpg",
        width=source.width,
        height=source.height,
        vegetation_pixels=vegetation_pixels,
        valid_pixels=valid_pixels,
        gvi_percent=gvi,
        vegetation_labels=result.labels,
        device=result.device,
        model=result.model,
        mask_png_base64=encode_png(render_mask(result.mask, result.vegetation_values)),
        overlay_png_base64=encode_png(
            render_overlay(source, result.mask, result.vegetation_values)
        ),
    )
