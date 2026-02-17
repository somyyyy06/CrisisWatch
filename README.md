# CrisisWatch

CrisisWatch is a full-stack crisis monitoring platform with a FastAPI backend and a React frontend. It supports user reports, live incident feeds, and WebSocket updates for new incidents.

## Features
- Report incidents with location and severity
- Live incident feed and GeoJSON map data
- User authentication with JWT
- WebSocket updates for new incidents
- Background scraping and ML scoring (Celery + Redis)

## Project Structure
- `app/` FastAPI backend, DB models, API routes, Celery tasks
- `frontend/` React app
- `app/alembic/` DB migrations
- `uploads/` stored uploads

## Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (optional, for Celery tasks)

## Environment Variables
Create a `.env` file in the project root (or export these in your shell):

```env
# Backend
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/crisiswatch
JWT_SECRET=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REDIS_URL=redis://localhost:6379/0
PORT=8000

# Frontend
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_WS_URL=ws://127.0.0.1:8000
```

Notes:
- `DATABASE_URL` is required for both the API and Alembic migrations.
- `REDIS_URL` is only needed if you run Celery workers/beat.
- Frontend defaults to `http://127.0.0.1:8000` when running on localhost.

## Setup (Backend)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Setup (Frontend)
```bash
cd frontend
npm install
npm start
```

The app runs at `http://localhost:3000` and connects to the API at `http://127.0.0.1:8000` by default.

## Background Tasks (Optional)
If you want scraping/ML tasks to run:
```bash
celery -A app.celery_app.celery worker --loglevel=info
celery -A app.celery_app.celery beat --loglevel=info
```

## API Endpoints (Quick Peek)
- `POST /auth/signup`
- `POST /auth/token`
- `GET /health`
- `GET /metrics/summary`
- `POST /incidents/submit`
- `GET /incidents/geojson`
- `GET /feed/live`
- `GET /subscriptions`

## Docker (Optional)
```bash
docker build -t crisiswatch .
docker run --env-file .env -p 8000:10000 crisiswatch
```

## Troubleshooting
- Alembic errors usually mean `DATABASE_URL` is missing or invalid.
- If the frontend shows API errors, confirm `REACT_APP_API_URL`.
- WebSocket issues: make sure `REACT_APP_WS_URL` uses `ws://` or `wss://`.

## License
MIT