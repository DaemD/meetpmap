# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies (upgrade pip first for better compatibility)
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model (prevents timeout on first request)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Expose port (platforms will set PORT env var)
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]


