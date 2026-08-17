FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directory & permissions for Hugging Face non-root user
RUN mkdir -p /app/cache /app/examples && \
    useradd -m -u 1000 user && \
    chown -R user:user /app

USER user

ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV CACHE_DIR=/app/cache

EXPOSE 7860

CMD ["python", "app.py"]
