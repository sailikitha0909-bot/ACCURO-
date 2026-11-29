import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api.auth import router as auth_router
from app.api.clients import router as clients_router
from app.api.documents import router as documents_router
from app.api.entries import router as entries_router
from app.api.exceptions import router as exceptions_router
from app.api.reconciliation import router as reconciliation_router
from app.api.reports import router as reports_router
from app.api.rules import router as rules_router
from app.api.audit import router as audit_router
from app.api.portal import router as portal_router
from app.api.dashboard import router as dashboard_router
from app.db.seed_data import seed_database

# Ensure tables and storage exist
Base.metadata.create_all(bind=engine)
os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Accuro — Production-grade multi-tenant web application for Indian CA firms. 'Accurate accounts. You review, Accuro does the rest.'",
    version=settings.VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development / production behind proxy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(clients_router, prefix=api_v1_prefix)
app.include_router(documents_router, prefix=api_v1_prefix)
app.include_router(entries_router, prefix=api_v1_prefix)
app.include_router(exceptions_router, prefix=api_v1_prefix)
app.include_router(reconciliation_router, prefix=api_v1_prefix)
app.include_router(reports_router, prefix=api_v1_prefix)
app.include_router(rules_router, prefix=api_v1_prefix)
app.include_router(audit_router, prefix=api_v1_prefix)
app.include_router(portal_router, prefix=api_v1_prefix)
app.include_router(dashboard_router, prefix=api_v1_prefix)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": "Accuro",
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "docs": "/docs",
        "health": "/health",
        "footer_disclaimer": "AI-prepared draft by Accuro. Requires CA review."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
