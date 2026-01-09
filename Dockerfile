# Python 3.10: matches development environment
FROM python:3.10-slim

# Metadata
LABEL maintainer="cabustillo13@hotmail.com"
LABEL description="Flight Delay Prediction API"
LABEL version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .

# Install dependencies - all have pre-built wheels for Python 3.10
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY challenge/ ./challenge/
COPY data/ ./data/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Cloud Run injects PORT variable, default to 8080
    PORT=8080 \
    HOST=0.0.0.0 \
    # Use multiple workers for better concurrency
    WORKERS=2

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=5)" || exit 1

# Run the application with Uvicorn
CMD uvicorn challenge.api:app --host ${HOST} --port ${PORT} --workers ${WORKERS}