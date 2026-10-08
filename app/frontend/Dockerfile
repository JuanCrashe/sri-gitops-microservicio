# STAGE 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# STAGE 2: Production
FROM python:3.11-slim

# Labels para trazabilidad
LABEL maintainer="TFM-UNIR-GitOps-Multicloud"
LABEL description="SRI Frontend - Portal de Contribuyentes"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Crear usuario no-root (seguridad)
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser appuser

WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /install /usr/local

# Copiar código de aplicación
COPY . .

# Cambiar ownership
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Comando de inicio
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:create_app()"]
