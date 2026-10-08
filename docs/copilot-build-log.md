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

## 2026-10-08 — Phase 3 hardening

- **Feature:** SegFormer logits post-processing at source dimensions, pixel-preserving overlays, decoded-image limits, backend-only Mapillary thumbnail analysis, bbox/pagination validation, and frontend loading/error/result tests.
- **Copilot use:** Implemented and corrected in Agent Mode from the Phase 3 review requirements. The frontend test isolation issue was fixed by adding Testing Library cleanup between tests. A Mapillary per-image lookup incompatibility was found during browser verification; the backend now reuses validated metadata from its permitted cache before attempting a detail lookup.
- **Relevant commit/PR:** Commits `c6d81c3` and `8a7592b` on branch `phase-3/segmentation-mapillary-hardening`, pushed to [the Phase 3 branch](https://github.com/aroraanushri/shady-walks/tree/phase-3/segmentation-mapillary-hardening). The review URL is [open a pull request](https://github.com/aroraanushri/shady-walks/compare/main...phase-3/segmentation-mapillary-hardening?expand=1); an authenticated GitHub session is required to submit it.
- **Issue:** The cloud-agent-ready issue draft is [07-phase-3-hardening.md](issues/07-phase-3-hardening.md). A GitHub issue number will be added after authenticated issue creation.
- **Test outcomes:** Backend Ruff passed; backend pytest passed with 15 tests. Frontend TypeScript typecheck passed; frontend tests passed with 2 tests; frontend production build passed.
- **Browser verification:** With local FastAPI and Vite servers, the browser loaded 3 real permitted Mapillary image locations after zooming into Pune. Marker `1197280535942719` displayed its real thumbnail, timestamp, coordinates, and `Mapillary / Absawant` attribution. Backend analysis returned 15.89% visible greenery, 124,957 vegetation pixels, 786,432 valid pixels, classes `tree, plant`, and `cpu`; the result and overlay were displayed in the UI.
- **Human-reviewed corrections:** No CUDA claim was made because the environment remains PyTorch `2.7.0+cpu`. The browser initially exposed a Mapillary detail-field incompatibility, which was fixed and reverified. A favicon 404 remained unrelated to the application workflow. License and Mapillary derived-data review remain open before public deployment.
