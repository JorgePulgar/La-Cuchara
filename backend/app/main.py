"""
backend/app/main.py
FastAPI entry point for La Cuchara backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, images, menus, restaurants

app = FastAPI(
    title="La Cuchara API",
    description="API para la plataforma de restaurantes La Cuchara",
    version="0.1.0",
)

# CORS middleware — allows the Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register routers ---
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(images.router, prefix="/images", tags=["images"])
app.include_router(menus.router, prefix="/menus", tags=["menus"])
app.include_router(restaurants.router, prefix="/restaurants", tags=["restaurants"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "La Cuchara API is running", "status": "ok"}
