# ============================================================
# SALES CRM MANAGEMENT
# Production Dockerfile
# React/Vite Frontend + Python/FastAPI Backend
# ============================================================


# ============================================================
# STAGE 1 — BUILD FRONTEND
# ============================================================

FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

# Copy package definition first for better Docker caching
COPY frontend/package.json ./

# Clean npm cache and install dependencies
# package-lock is intentionally not required
RUN npm cache clean --force \
    && npm install \
        --no-audit \
        --no-fund \
        --package-lock=false \
        --legacy-peer-deps

# Copy complete frontend source
COPY frontend/ ./

# Build React/Vite application
RUN npm run build


# ============================================================
# STAGE 2 — PYTHON BACKEND
# ============================================================

FROM python:3.12-slim

WORKDIR /app

# Python production settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Railway provides PORT dynamically
ENV PORT=8000


# ============================================================
# BACKEND DEPENDENCIES
# ============================================================

COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
       -r /app/backend/requirements.txt


# ============================================================
# BACKEND SOURCE
# ============================================================

COPY backend/ /app/backend/


# ============================================================
# FRONTEND PRODUCTION BUILD
# ============================================================

COPY --from=frontend-builder \
    /build/frontend/dist \
    /app/frontend/dist


# ============================================================
# APPLICATION DIRECTORY
# ============================================================

WORKDIR /app/backend


# ============================================================
# NETWORK
# ============================================================

EXPOSE 8000


# ============================================================
# START APPLICATION
# ============================================================

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
