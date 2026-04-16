# La Cuchara 🍽️

> 🌐 [Versión en español](README_ES.md)

A full-stack web application that digitizes restaurant menus using OCR and predicts daily offerings using machine learning. Restaurants upload photos of their menus; the system extracts the data automatically and makes it searchable by location and filters.

## What it does

- **OCR pipeline**: extracts structured menu data (dishes, prices, categories) from restaurant menu photos using Azure Computer Vision
- **ML predictions**: predicts likely daily menu offerings based on historical menu data using a scikit-learn classification pipeline
- **Location-based discovery**: users find nearby restaurants and browse their menus with filters
- **Restaurant management**: restaurants upload menu photos and manage their listings

## Project Structure

```
├── frontend/      # Next.js (App Router) + React + TypeScript + Tailwind CSS
├── backend/       # FastAPI (Python) + Pydantic v2
└── LaCuchara/     # Additional app resources
```

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js · React · TypeScript · Tailwind CSS |
| Backend | FastAPI · Python · Pydantic v2 |
| Database | Supabase (PostgreSQL) |
| OCR | Azure Computer Vision |
| ML | scikit-learn · RandomForestClassifier · LogisticRegression · Pipeline · OneHotEncoder · StandardScaler |

## Setup

### Backend

```bash
cd backend
cp .env.example .env
# Fill in your Supabase and Azure Computer Vision credentials in .env
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
