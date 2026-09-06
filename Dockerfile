# Tahap 1: Build Frontend (React / Vite)
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Tahap 2: Setup Backend Python
FROM python:3.10-slim
WORKDIR /app

# Install dependencies backend
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Salin seluruh kode backend
COPY backend/ ./backend/

# Salin hasil build frontend (dist) dari tahap 1 ke dalam folder backend
COPY --from=frontend-builder /app/frontend/dist ./backend/dist

# Masuk ke folder backend agar server berjalan dari sana
WORKDIR /app/backend

# Jalankan server menggunakan Uvicorn
EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
