"""
Clawback Backend Application Entry Point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.config import settings
from backend.app.database import engine, Base
import backend.app.models  # ensure all models are registered
from backend.app.api.contracts import router as contracts_router
from backend.app.api.invoices import router as invoices_router
from backend.app.api.audit import router as audit_router
from backend.app.api.dispute import router as dispute_router
from backend.app.api.amd_status import router as amd_status_router


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create SQLite / PostgreSQL database tables
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Deterministic Carrier Contract Audit & Overcharge Recovery Engine powered by AMD & Gemma",
    version="1.0.0",
    lifespan=lifespan
)

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(contracts_router)
app.include_router(invoices_router)
app.include_router(audit_router)
app.include_router(dispute_router)
app.include_router(amd_status_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "llm_mode": settings.LLM_MODE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
