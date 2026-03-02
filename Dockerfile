# syntax=docker/dockerfile:1.2  # enable BuildKit features such as secrets
# Use official Python image as base
FROM python:3.12

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2 and audio support if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Expose any ports used by the keep-alive Flask server (default 8080)
EXPOSE 8080

# Default command to run the bot
CMD ["python", "main.py"]
