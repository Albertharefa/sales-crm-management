FROM node:18-slim

# Install Python dan pip
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Salin seluruh file proyek ke dalam container
COPY . /app

# Masuk ke folder frontend dan instal semua modul secara lengkap
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Pindah ke root untuk setup backend Python
WORKDIR /app

# Install dependencies Python backend
RUN pip3 install --no-cache-dir -r backend/requirements.txt --break-system-packages

# Salin hasil build frontend ke dalam folder backend
RUN cp -r /app/frontend/dist /app/backend/dist

# Jalankan server
WORKDIR /app/backend
EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
