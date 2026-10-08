# ShadeShift

Find the greener way home using observed street-level imagery.

ShadeShift is an open-source Pune pilot that runs local semantic segmentation on permitted imagery and reports a **Green View Index (GVI)**: visible vegetation pixels divided by valid image pixels. It does not predict temperature, thermal comfort, or guaranteed shade.

## Phase 1 quick start

### Backend

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The first real analysis downloads the Hugging Face checkpoint and requires enough disk/RAM. GPU inference uses CUDA automatically; CPU is supported but slower. Tests never download model weights:

```powershell
pytest
ruff check .
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` when the API is not running on `http://localhost:8000`.

## Data and limitations

Mapillary integration is planned for Phase 2. Any imagery provider must be used through its documented API, with attribution, timestamps, licensing, and coverage uncertainty preserved. Uploaded photographs remain local to the running service and are not committed.

## Development

- Repository-specific Copilot guidance: `.github/copilot-instructions.md`
- CI: `.github/workflows/ci.yml`
- Planned work: `docs/issues/`
- Verified Copilot contributions: `docs/copilot-build-log.md`
- Submission evidence placeholders: `docs/hacktoberfest-submission.md`