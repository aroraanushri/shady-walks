from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    filename: str
    width: int
    height: int
    vegetation_pixels: int
    valid_pixels: int
    gvi_percent: float = Field(ge=0, le=100)
    vegetation_labels: list[str]
    device: str
    model: str
    mask_png_base64: str
    overlay_png_base64: str
    observed_only: bool = True
    limitation: str = (
        "GVI measures visible vegetation in this image only. It is not a temperature, "
        "shade, or thermal-comfort prediction."
    )
