from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
import os
import socket
from datetime import datetime, timezone

app = FastAPI(
    title="Microservicio SRI",
    description="API de Gestión de Contribuyentes",
    version="1.0.0"
)

# Configurar CORS (necesario si el frontend accede directamente o desde otro origen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "SRI Facturación Service API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check para Kubernetes liveness probe"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check para Kubernetes"""
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Endpoint para Prometheus metrics (básico)"""
    return {
        "requests_total": 0,
        "uptime_seconds": 0
    }

@app.get("/api/v1/version")
async def get_version(request: Request):
    """
    Endpoint clave para demostrar portabilidad multi-cloud.
    Retorna la versión y el cloud provider donde está corriendo.
    """
    cloud_provider = os.getenv("CLOUD_PROVIDER", "unknown")
    cluster_name = os.getenv("CLUSTER_NAME", "unknown")
    
    return {
        "version": "1.0.0",
        "cloud": cloud_provider,
        "cluster": cluster_name,
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/info")
async def get_info():
    """Información del entorno de ejecución"""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "cloud_provider": os.getenv("CLOUD_PROVIDER", "unknown"),
        "region": os.getenv("CLOUD_REGION", "unknown"),
        "python_version": os.sys.version,
        "platform": os.sys.platform
    }
