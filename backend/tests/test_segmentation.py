import numpy as np
from PIL import Image

from app.segmentation import calculate_gvi, is_vegetation_label, render_mask


def test_calculate_gvi_uses_valid_pixels_and_vegetation_classes() -> None:
    mask = np.array([[1, 1, 2], [0, -1, 2]])

    vegetation, valid, gvi = calculate_gvi(mask, {1})

    assert (vegetation, valid, gvi) == (2, 5, 40.0)


def test_render_mask_marks_only_observed_vegetation() -> None:
    rendered = render_mask(np.array([[1, 0], [-1, 2]]), {1})

    assert isinstance(rendered, Image.Image)
    assert rendered.getpixel((0, 0))[:3] == (39, 174, 96)
    assert rendered.getpixel((1, 0))[3] == 0
    assert rendered.getpixel((0, 1))[:3] == (120, 120, 120)


def test_vegetation_label_matching_does_not_match_substrings() -> None:
    assert is_vegetation_label("tree")
    assert is_vegetation_label("potted plant")
    assert not is_vegetation_label("streetlight")
