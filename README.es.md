# La Cuchara 🍽️

> 🌐 [English version](README.md)

Aplicación web full-stack que digitaliza menús de restaurantes usando OCR y predice las ofertas diarias mediante machine learning. Los restaurantes suben fotos de sus menús; el sistema extrae los datos automáticamente y los hace buscables por ubicación y filtros.

Construida como proyecto de grupo de 2–3 semanas para el máster de Tajamar, junto con [Íñigo](https://github.com/isaji-23).

## Qué hace

- **Pipeline OCR**: extrae datos estructurados del menú (platos, precios, categorías) a partir de fotos de menús de restaurantes usando Azure Computer Vision
- **Predicciones ML**: predice las ofertas probables del menú diario a partir del histórico de menús usando un pipeline de clasificación con scikit-learn
- **Búsqueda por ubicación**: los usuarios encuentran restaurantes cercanos y exploran sus menús con filtros
- **Gestión para restaurantes**: los restaurantes suben fotos de sus menús y gestionan sus listados

## Estructura del proyecto

```
├── frontend/      # Next.js (App Router) + React + TypeScript + Tailwind CSS
├── backend/       # FastAPI (Python) + Pydantic v2
└── LaCuchara/     # Recursos adicionales de la aplicación
```

## Stack

| Capa | Tecnología |
|-------|-----------|
| Frontend | Next.js · React · TypeScript · Tailwind CSS |
| Backend | FastAPI · Python · Pydantic v2 |
| Base de datos | Supabase (PostgreSQL) |
| OCR | Azure Computer Vision |
| ML | scikit-learn · RandomForestClassifier · LogisticRegression · Pipeline · OneHotEncoder · StandardScaler |

## Instalación

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
# Rellena tus credenciales de Supabase y de la API en .env.local
npm install
npm run dev
```

## Variables de entorno

Consulta `backend/.env.example` y `frontend/.env.local.example` para las variables requeridas.

## Base de datos

El esquema SQL para Supabase está en `backend/supabase_schema.sql`.

## Autores

- [Jorge Pulgar](https://github.com/JorgePulgar)
- [Íñigo](https://github.com/isaji-23)
