# Backend (FastAPI)

This folder contains a minimal FastAPI backend with a virtual environment setup.

Quick start (PowerShell):

```powershell
cd backend
# create venv (only if not already created)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# run app
uvicorn app.main:app --reload --port 8000
```

Run tests:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```
