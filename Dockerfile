FROM python:3.10-slim

WORKDIR /app

# Salin folder backend
COPY backend/ ./backend/

WORKDIR /app/backend

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
