# ShadeShift repository instructions

## Product and architecture

ShadeShift identifies observed vegetation in permitted, geotagged street imagery. Keep the backend (`backend/`) responsible for image validation, inference, GVI calculations, and provenance; keep the frontend (`frontend/`) responsible for map-first presentation and user interaction.

## Model and inference rules

- Use Hugging Face Transformers with `nvidia/segformer-b0-finetuned-ade-512-512` for the production segmenter.
- Read the checkpoint's `id2label` mapping at runtime; never hard-code a vegetation class index.
- Prefer CUDA when available and fall back to CPU.
- Load the model lazily so health checks, tests, and the web UI do not download weights.
- GVI is `(vegetation pixels / valid image pixels) * 100`. It describes visible vegetation only, never temperature, shade, or thermal comfort.
- Preserve original images, masks, overlays, timestamps, and attribution when adding imagery providers.

## Code quality and safety

- Python 3.11, type hints, Ruff, pytest; TypeScript strict mode and ESLint.
- Validate uploads by content and size, use explicit error responses, and avoid broad exception handling.
- Keep external APIs behind small clients with dependency injection so tests use fixtures and mocks.
- Never add credentials, downloaded model weights, user images, or generated results to git.
- Do not fabricate coverage, field observations, route statistics, or model evaluations.

## Testing

Unit tests must use synthetic masks and mocked model/API responses. CI must pass without Mapillary credentials, a GPU, or a model download. Add integration tests only when they can run deterministically with local fixtures.

## Documentation conventions

Document reproducible setup, data licensing/attribution, limitations, and uncertainty. Record actual Copilot contributions and human verification in `docs/copilot-build-log.md`; do not backfill claims about tools or results that did not occur.
