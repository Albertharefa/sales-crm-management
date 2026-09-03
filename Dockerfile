# ============================================================
# Sales CRM Management - Production image for Railway
# Multi-stage build: Vite/React frontend + FastAPI backend
# ============================================================

FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package.json ./
RUN npm install --no-audit --no-fund --prefer-offline

COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first for better Docker layer caching.
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/backend/requirements.txt

# Backend source
COPY backend/ /app/backend/

# Compiled React application
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

WORKDIR /app/backend

# Railway provides PORT at runtime.
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
