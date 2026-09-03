# Menggunakan image Python versi ringan (slim)
FROM python:3.11-slim

# Menyiapkan folder kerja di dalam server
WORKDIR /app

# Menghindari Python membuat file cache (.pyc) dan memastikan log langsung tercetak
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Menyalin file daftar kebutuhan (library)
COPY backend/requirements.txt .

# Menginstal library tanpa menyimpan cache instalasi agar file lebih kecil
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh folder backend ke dalam server
COPY backend/ .

# Membuka port yang akan digunakan
EXPOSE 8000

# Perintah untuk menjalankan server FastAPI dengan uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
