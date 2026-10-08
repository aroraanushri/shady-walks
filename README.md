# ShadeShift

Find the greener way home using observed street-level imagery.

ShadeShift is an open-source Pune pilot that runs local semantic segmentation on permitted imagery and reports a **Green View Index (GVI)**: visible vegetation pixels divided by valid image pixels. It does not predict temperature, thermal comfort, or guaranteed shade.

## Local end-to-end quick start

### Backend

```powershell
Set-Location .\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
# Edit .env and set MAPILLARY_TOKEN to your Mapillary client token.
python -m uvicorn app.main:app --reload
```

The first real analysis downloads the Hugging Face checkpoint and requires enough disk/RAM. GPU inference uses CUDA automatically; CPU is supported but slower. Tests never download model weights:

```powershell
pytest
ruff check .
```

### Frontend

```powershell
Set-Location ..\frontend
npm install
npm run dev
```

Set `VITE_API_URL` when the API is not running on `http://localhost:8000`.

Open the Vite URL shown in the terminal, normally `http://localhost:5173`. The map starts at Pune; use **Load imagery in this area** after panning or zooming. Mapillary credentials remain in the backend `.env` only.

## Data and limitations

Mapillary imagery is retrieved through the documented Graph API with a backend-only token, bounded requests, one-hour metadata caching, duplicate/spatial sampling, timestamps, coordinates, image IDs, and attribution. The map reports missing imagery and API failures instead of fabricating coverage. Mapillary data and derived data must be used and shared according to Mapillary's current terms and CC BY-SA obligations; review those terms before publishing results.

Run the real local smoke test after configuring `.env`:

```powershell
python scripts/real_inference_smoke.py
```

It retrieves at most 10 actual images near VIT Pune, downloads one permitted thumbnail, runs SegFormer, and writes untracked artifacts under `backend/.local-results/`. CUDA is used when the installed PyTorch build supports it; otherwise the result explicitly records CPU fallback.

## Development

- Repository-specific Copilot guidance: `.github/copilot-instructions.md`
- CI: `.github/workflows/ci.yml`
- Planned work: `docs/issues/`
- Verified Copilot contributions: `docs/copilot-build-log.md`
- Submission evidence placeholders: `docs/hacktoberfest-submission.md`