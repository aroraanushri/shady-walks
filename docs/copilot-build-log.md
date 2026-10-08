# Copilot build log

This log records verified work only. Entries are added after implementation and review; no Copilot contribution, PR, benchmark, or field result is inferred.

## 2026-10-08 — Phase 1 foundation

- **Feature:** Repository instructions, FastAPI upload/inference API, React upload UI, tests, and CI.
- **Copilot use:** This initial implementation was produced in Copilot Agent Mode from the ShadeShift product brief.
- **Relevant commit/PR:** _To be filled after a real commit or pull request._
- **Problems and human review:** The initial frontend build lacked Vite's `ImportMetaEnv` types; the type declaration was added and the API test path was checked for mocked inference. Ruff's FastAPI dependency-injection warning was reviewed and suppressed only on the route parameter.
- **Test outcomes:** Backend `pytest`: 5 passed. Backend `python -m ruff check .`: passed after the lint fix. Frontend `npm test`: 1 passed; `npm run typecheck`: passed; `npm run build`: passed.

## 2026-10-08 — Mapillary and integration path

- **Feature:** Backend Mapillary Graph API client, bounded VIT Pune search, metadata cache, spatial sampling, Leaflet map markers, image inspector, and real-inference smoke script.
- **Copilot use:** Implemented in Agent Mode from the requested Mapillary and end-to-end verification requirements.
- **Verified environment facts:** The configured Mapillary token authenticated successfully against the Graph API and returned 10 image IDs in the Pune bbox. The installed PyTorch build was `2.7.0+cpu`, with CUDA unavailable; no RTX 5070 CUDA claim is made.
- **Model licensing:** The Hugging Face model card links the upstream NVlabs SegFormer license. Redistribution and public-use attribution still require human review of that license.
- **Real inference result:** The smoke test downloaded and ran `nvidia/segformer-b0-finetuned-ade-512-512` on Mapillary image `253242129918278` (`Mapillary / cartofy`). Source and corrected output mask were both 1024×768. Verified result: `tree` was the only detected vegetation class, 123,984 vegetation pixels of 786,432 valid pixels, 15.77% GVI, CPU device, and 11,149.5 ms inference latency on this CPU-only environment. The RTX 5070 was not used because the installed PyTorch build reports no CUDA support.
- **API verification:** A temporary local Uvicorn server returned `/health` 200. A fresh Mapillary thumbnail posted to `/api/analyze` returned 1024×768 dimensions, 22.14% GVI, 174,096 vegetation pixels of 786,432 valid pixels, `tree` as the vegetation class, and `cpu`. Overlay and mask PNGs were returned as base64 fields.
- **Human review:** _Verify Mapillary attribution and derived-data obligations before publishing cached metadata or analysis results._
