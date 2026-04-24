"""
Open Clinic AI — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    yield


app = FastAPI(
    title="Open Clinic AI",
    description="Sistema open-source para clínicas — API Backend",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.modules.auth.router import router as auth_router
from app.modules.admin.router import router as specialties_router
from app.modules.scheduling.router import router as scheduling_router
from app.modules.crm.router import router as patients_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(specialties_router, prefix="/api/v1/specialties", tags=["specialties"])
app.include_router(scheduling_router, prefix="/api/v1/scheduling", tags=["scheduling"])
app.include_router(patients_router, prefix="/api/v1/patients", tags=["patients"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
