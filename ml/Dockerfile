# Lightweight Python base image for ML inference
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python ML dependencies
COPY ml/requirements.txt ml/
RUN pip install --no-cache-dir -r ml/requirements.txt

# Copy ML package and pre-trained models
COPY ml/ ml/

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PROMETHEUS_URL=http://prometheus:9090
ENV MODEL_DIR=ml/models
ENV POLL_INTERVAL=10

EXPOSE 8000

CMD ["python", "ml/detector_service.py"]
