# Phase 3 — Inference and Mapillary hardening

## Goal

Make the existing ShadeShift map and image-analysis workflow safe and reliable
for a public review deployment without replacing the Phase 1/2 application.

## Acceptance criteria

- SegFormer semantic logits are resized to the source image dimensions before
  `argmax`; use the processor's semantic-segmentation post-processing API when
  available.
- Overlay PNGs preserve original non-vegetation pixels where the vegetation
  mask is transparent.
- Mapillary image analysis stays backend-only and accepts only validated numeric
  image IDs and approved HTTPS Mapillary thumbnail origins.
- Mapillary search requests enforce coordinate ranges, bounded bbox dimensions,
  bounded result limits, safe pagination hosts, timeouts, and useful API errors.
- Uploads and downloaded thumbnails enforce compressed byte and decoded-pixel
  limits and reject malformed image data.
- Frontend tests cover loading, successful GVI display, image selection,
  analysis/API errors, and the selected-image analysis state.
- CI remains independent of Mapillary credentials, GPU hardware, and model
  downloads.

## Verification

Run from PowerShell:

```powershell
Set-Location .\backend
python -m ruff check .
python -m pytest
Set-Location ..\frontend
npm run typecheck
npm test -- --run
npm run build
```

## Security and review notes

- Keep `MAPILLARY_TOKEN` in the backend environment only.
- Do not commit model weights, credentials, cached imagery, or generated
  analysis results.
- Review Mapillary attribution, licensing, and derived-data obligations before
  public deployment.
- Record actual browser and API verification results in
  `docs/copilot-build-log.md`; do not infer coverage or model quality.
