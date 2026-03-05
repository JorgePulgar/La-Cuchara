# La Cuchara 🍽️

A web application that helps users find nearby restaurants and explore their menus.

## Project Structure

- `frontend/` — Next.js (App Router) + React + TypeScript + Tailwind CSS
- `backend/` — FastAPI (Python) + Pydantic v2

## Setup

### Backend

```bash
cd backend
cp .env.example .env
# Fill in your Supabase credentials in .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Fill in your Supabase and API credentials in .env.local
npm install
npm run dev
```

## Environment Variables

See `backend/.env.example` and `frontend/.env.local.example` for required variables.

## Database

The SQL schema for Supabase is at `backend/supabase_schema.sql`.

## Status

See `TASKS.md` for development progress and `AGENT_STATUS.log` for any known issues.
