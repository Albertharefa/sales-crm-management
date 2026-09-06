FROM python:3.10-slim

WORKDIR /app

# Salin seluruh folder backend
COPY backend/ ./backend/

# Jika folder dist frontend sudah ada di lokal/repo, salin ke backend
# (Jika belum ada, server akan otomatis menampilkan pesan API running agar tidak crash)
COPY backend/dist/ ./backend/dist/ 2>/dev/null || true

WORKDIR /app/backend

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
