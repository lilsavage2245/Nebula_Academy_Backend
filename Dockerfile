# Dockerfile
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
    libjpeg62-turbo-dev zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy deps first for caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install deps
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . /app/

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

# Default command (compose overrides this for gunicorn/worker/beat)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
