# ============================================================
# Sales CRM Management - Production Image
# FastAPI + React/Vite + MongoDB (external Railway MongoDB)
# ============================================================

# ---------- Frontend build ----------
FROM node:22-bookworm-slim AS frontend-builder
WORKDIR /build/frontend

COPY frontend/package.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
ENV VITE_API_URL=/api
RUN npm run build


# ---------- Backend runtime ----------
FROM python:3.13-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PYTHONPATH=/app/backend     APP_ENV=production     PORT=8080

# Minimal runtime packages.
RUN apt-get update     && apt-get install -y --no-install-recommends curl     && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

EXPOSE 8080

# Railway provides PORT; uvicorn binds to all interfaces.
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
