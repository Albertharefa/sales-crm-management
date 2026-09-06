FROM python:3.10-slim

# Install Node.js agar bisa build frontend
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Salin seluruh isi project
COPY . /app

# Build Frontend (React / Vite)
RUN cd frontend && npm install && npm run build

# Install Dependencies Backend
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pindahkan hasil build frontend ke folder backend agar terbaca server
RUN cp -r frontend/dist backend/dist || true

WORKDIR /app/backend

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
