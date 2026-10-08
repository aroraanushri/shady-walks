# Backend and segmentation pipeline

## Acceptance criteria

- `POST /api/analyze` validates image type and size.
- SegFormer B0 loads lazily through Transformers and uses CUDA when available.
- Vegetation classes come from the checkpoint label mapping.
- Response contains original dimensions, mask, overlay, observed GVI, device, and limitations.
- Unit tests use mocked inference and synthetic masks.
