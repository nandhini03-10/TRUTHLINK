# TruthLink: Verified-Source Rumor Verification Engine

A prototype full-stack MVP for rumor verification using official and verified sources.

## Architecture

- Frontend: Next.js + Tailwind CSS
- Backend: FastAPI
- Verification pipeline: Claim analysis, entity extraction, stakeholder lookup, evidence collection, truth scoring, explainable output

## Run locally (Python-only)

1. Backend CLI

```powershell
cd backend
python -m pip install -r requirements.txt
python -m truthlink "Tesla is shutting down its India operations."
```

2. Optional API server

```powershell
cd backend
python -m pip install fastapi uvicorn[standard] pydantic>=2.7.0
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Open browser for API docs

- Backend API docs: http://localhost:8000/docs

## Project structure

- `backend/app`: API and verification engine
- `frontend`: Next.js application

## Example claim

`Tesla is shutting down operations in India.`
