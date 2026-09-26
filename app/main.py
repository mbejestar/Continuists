from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.routers import api_router

app = FastAPI(
    title="CONTINUUM API",
    description="Knowledge Preservation & Controlled Marketplace Platform. 'The files remain. The context doesn't.'",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Mount API Routers under /api
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "platform": "CONTINUUM",
        "tagline": "The files remain. The context doesn't.",
        "version": "1.0.0",
        "api_docs": "/api/docs",
        "jurisdiction": "South Africa (POPIA & IP Compliant)",
        "currency": "ZAR"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "continuum-api"}
