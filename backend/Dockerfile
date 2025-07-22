# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with timeout and retry settings
RUN pip install --no-cache-dir --timeout=1000 --retries=5 -r requirements.txt

# Copy the entire backend directory
COPY . .

# Create necessary directories
RUN mkdir -p processed_data prods_fastapi/data

# Expose port 8000
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Command to run the application
# Use PORT environment variable for Render compatibility
CMD python -m uvicorn prods_fastapi.main:app --host 0.0.0.0 --port ${PORT:-8000}
