FROM node:18-slim

# Install Python dan pip di dalam image Node.js
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Salin seluruh file project
COPY . /app

# Build Frontend
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Pindah ke backend dan instal dependencies Python
WORKDIR /app/backend
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Salin hasil build frontend ke folder backend
RUN cp -r /app/frontend/dist /app/backend/dist

# Jalankan server
EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
