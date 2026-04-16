# La Cuchara 🍽️

Una aplicación web full-stack que digitaliza cartas de restaurantes mediante OCR y predice los menús del día usando machine learning. Los restaurantes suben fotos de sus cartas; el sistema extrae los datos automáticamente y los hace buscables por ubicación y filtros.

## Qué hace

- **Pipeline OCR**: extrae datos estructurados (platos, precios, categorías) a partir de fotos de cartas de restaurante usando Azure Computer Vision
- **Predicciones ML**: predice los platos probables del menú diario basándose en datos históricos mediante un pipeline de clasificación con scikit-learn
- **Búsqueda por ubicación**: los usuarios encuentran restaurantes cercanos y exploran sus cartas con filtros
- **Gestión para restaurantes**: los restaurantes suben fotos de sus cartas y gestionan sus fichas

## Estructura del proyecto

```
├── frontend/      # Next.js (App Router) + React + TypeScript + Tailwind CSS
├── backend/       # FastAPI (Python) + Pydantic v2
└── LaCuchara/     # Recursos adicionales de la app
```

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js · React · TypeScript · Tailwind CSS |
| Backend | FastAPI · Python · Pydantic v2 |
| Base de datos | Supabase (PostgreSQL) |
| OCR | Azure Computer Vision |
| ML | scikit-learn · RandomForestClassifier · LogisticRegression · Pipeline · OneHotEncoder · StandardScaler |

## Configuración

### Backend

```bash
cd backend
cp .env.example .env
# Rellena tus credenciales de Supabase y Azure Computer Vision en .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Rellena tus credenciales de Supabase y API en .env.local
npm install
npm run dev
```

## Variables de entorno

Consulta `backend/.env.example` y `frontend/.env.local.example` para las variables necesarias.

## Base de datos

El esquema SQL para Supabase está en `backend/supabase_schema.sql`.
