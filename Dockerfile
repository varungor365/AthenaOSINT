# Base Image
FROM python:3.9-slim-buster

# Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run_web.py
ENV FLASK_ENV=production

# Work Directory
WORKDIR /app

# System Dependencies (for tools like ExifTool and builds)
RUN apt-get update && apt-get install -y \
    libexif-bin \
    exiftool \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy Project
COPY . .

# Expose Web Port
EXPOSE 5000

# Default Command (Run Daemon + Web via a supervisor approach or just the web for now)
# Ideally we use supervisord, but for simplicity:
CMD ["python", "run_web.py"]
