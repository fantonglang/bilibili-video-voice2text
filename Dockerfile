# Bilibili Video Voice to Text - Docker Image
# Usage: docker build -t bili-voice2text .

# Using Python 3.11 slim (more widely available)
FROM python:3.11-slim

# Install system dependencies
# - ffmpeg: Required for moviepy audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories (will be mounted as volumes)
RUN mkdir -p bilibili_video audio/conv audio/slice outputs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command (can be overridden)
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
