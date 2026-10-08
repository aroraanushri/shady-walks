from __future__ import annotations

import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from .schemas import AnalysisResponse
from .segmentation import (
    SegFormerSegmenter,
    calculate_gvi,
    encode_png,
    render_mask,
    render_overlay,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
segmenter = SegFormerSegmenter()
app = FastAPI(title="ShadeShift API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shadeshift-api"}


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
