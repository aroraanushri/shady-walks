import numpy as np
import torch
from PIL import Image

from app.segmentation import (
    SegFormerSegmenter,
    calculate_gvi,
    is_vegetation_label,
    render_mask,
    render_overlay,
)


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


def test_predict_uses_processor_postprocessing_at_source_size() -> None:
    calls: list[list[tuple[int, int]]] = []

    class Processor:
        def __call__(self, **_: object) -> object:
            class Inputs(dict):
                def to(self, _: object) -> "Inputs":
                    return self

            return Inputs()

        def post_process_semantic_segmentation(
            self, _outputs: object, target_sizes: list[tuple[int, int]]
        ) -> list[torch.Tensor]:
            calls.append(target_sizes)
            return [torch.tensor([[1, 0, 1], [0, 1, 0]], dtype=torch.int64)]

    class Model:
        config = type("Config", (), {"id2label": {0: "road", 1: "tree"}})()

        def eval(self) -> None:
            return None

        def __call__(self, **_: object) -> object:
            return {}

    segmenter = SegFormerSegmenter()
    segmenter._processor = Processor()
    segmenter._model = Model()
    segmenter._device = torch.device("cpu")

    result = segmenter.predict(Image.new("RGB", (3, 2)))

    assert calls == [[(2, 3)]]
    assert result.mask.shape == (2, 3)
    assert result.labels == ["tree"]


def test_render_overlay_preserves_original_non_vegetation_pixels() -> None:
    source = Image.new("RGB", (2, 1), (12, 34, 56))
    source.putpixel((1, 0), (90, 80, 70))

    overlay = render_overlay(source, np.array([[0, 1]]), {1})

    assert overlay.getpixel((0, 0)) == (12, 34, 56, 255)
    assert overlay.getpixel((1, 0)) != (90, 80, 70, 255)
