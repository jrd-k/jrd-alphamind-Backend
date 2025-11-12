# jrd-alphamind-backend (scaffold)

This is a small scaffold for the jrd-alphamind backend. It contains a FastAPI app and placeholder modules for API routes, models, services, workers and ML.

Quick start (requires Python 3.11+):

1. create virtualenv and install deps

   python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt

2. run the app

   uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs for the interactive API docs.
