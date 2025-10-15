# Python 3.11 als Basis
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Kopiere requirements.txt und installiere Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere alle Backend-Dateien
COPY . .

# Expose Port 8000 (Standard für FastAPI)
EXPOSE 8000

# Starte FastAPI mit Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
