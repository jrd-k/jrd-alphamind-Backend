# Running the full stack (backend + frontend)

This repo contains a FastAPI backend in `backend/` and a Vite React frontend in
`frontend/`.

Quick start (Windows PowerShell):

1. Create and activate Python venv, install backend deps

```powershell
cd c:\Users\USER\jrd-alphamind-Backend\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Install frontend deps and start Vite

```powershell
cd c:\Users\USER\jrd-alphamind-Backend\frontend
npm install
# ensure API base matches backend host/port
$env:VITE_API_BASE_URL = 'http://localhost:8000'
npm run dev
```

3. Start backend

```powershell
cd c:\Users\USER\jrd-alphamind-Backend\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the convenience scripts in `scripts/` from the repo root:

```powershell
# open two consoles and let them run
cd c:\Users\USER\jrd-alphamind-Backend\scripts
# start backend in a new PS window and frontend in another
.\start-all.ps1
```

Notes:
- The backend defaults to sqlite (file `dev.db`).
- The frontend reads `VITE_API_BASE_URL` at build/dev time to determine the API
  base URL.
- Tests are under `backend/tests`.  A `conftest.py` has been added to help
  pytest find the backend package and optionally start a live server for
  integration tests.

Docker Compose (development)

I added `docker-compose.dev.yml` to run the stack in containers for local
development or CI. The compose file starts Postgres, Redis, the backend and
the frontend. To start the full stack:

```powershell
cd c:\Users\USER\jrd-alphamind-Backend
docker compose -f docker-compose.dev.yml up --build
```

The frontend will be exposed on `http://localhost:8081` and the backend on
`http://localhost:8000`.

Notes:
- The backend container reads `DATABASE_URL` from the compose file and will
  connect to the `postgres` service. If you prefer to keep using sqlite, use
  the venv local instructions above instead.
- For CI you can use the same compose file to run tests against the containerized
  backend by running `docker compose -f docker-compose.dev.yml run backend pytest`.

If you want an nginx reverse proxy or additional services (SMTP, mock brokers,
or more realistic broker simulations), I can add them next.
