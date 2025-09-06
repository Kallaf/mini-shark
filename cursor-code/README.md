# Mini Shark Backend (FastAPI)

FastAPI backend for a Shark Tank-like simulator where users chat with AI shark bots, spend coins per session, and can purchase more coins. Includes PostgreSQL with SQLAlchemy/Alembic and Pydantic schemas.

## Features

- Users identified by `X-User-Email` header, auto-provisioned with 200 coins
- List sharks with price/personality/expertise/image
- Start paid chat sessions with sharks (coins deducted)
- Send/receive chat messages (stubbed AI reply)
- Session report field
- History counters and paginated sessions with filters
- Simulated coin purchases
- Alembic migrations and seed data for sharks

## Requirements

- Python 3.10+
- PostgreSQL 13+

## Setup

1) Create and activate virtual environment
```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure database
- Create a PostgreSQL database, e.g., `mini_shark`
- Set `DATABASE_URL` (or edit `app/core/config.py`)
```bash
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/mini_shark"
```

4) Run migrations
```bash
alembic upgrade head
```

5) Run server
```bash
uvicorn app.main:app --reload --port 8000
```

## API Overview

- GET `/api/v1/users/me`
- POST `/api/v1/users/me/purchases` { coins }
- GET `/api/v1/sharks`
- POST `/api/v1/sharks/{shark_id}/start`
- GET `/api/v1/sessions/{session_id}`
- POST `/api/v1/sessions/{session_id}/messages` { content }
- GET `/api/v1/history/counters`
- GET `/api/v1/history/sessions`

All endpoints require header `X-User-Email: you@example.com`.

## Notes

- AI replies are stubbed. Replace `app/services/ai.py` to integrate an LLM.
- Coin pricing per USD is simulated; adjust `COINS_PER_USD` in `app/core/config.py`.
