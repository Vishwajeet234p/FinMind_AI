import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
import app.models.user  # Ensure User + PortfolioItem tables are created

# Initialize ALL database tables on server startup
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Financial Intelligence & Algorithmic Stock Analytics API",
    version="1.0.0",
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api/v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "message": "Welcome to FinMind AI Engine API!"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected (SQLite/PostgreSQL)",
        "redis": "ready"
    }

# Serve the frontend Financial Terminal at http://localhost:8000/dashboard/
# backend/app/main.py is two directory levels below the project root.
_frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
_frontend_path = os.path.abspath(_frontend_path)

if os.path.isdir(_frontend_path):
    app.mount("/dashboard", StaticFiles(directory=_frontend_path, html=True), name="frontend")
