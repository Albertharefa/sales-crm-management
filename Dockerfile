FROM python:3.10-slim

# Install Node.js dan npm
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Salin seluruh file proyek ke dalam container
COPY . /app

# Masuk ke folder frontend dan pastikan semua dependencies (termasuk tailwindcss/vite) terpasang
WORKDIR /app/frontend
RUN npm install
RUN npm install @tailwindcss/vite --save
RUN npm run build

# Kembali ke root /app
WORKDIR /app

# Install dependencies Python backend
RUN pip install --no-cache-dir -r backend/requirements.txt

# Salin hasil build frontend (dist) langsung ke dalam folder backend
RUN cp -r frontend/dist backend/dist

# Jalankan server backend
WORKDIR /app/backend
EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
