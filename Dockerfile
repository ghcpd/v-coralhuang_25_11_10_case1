FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set Python to unbuffered mode
ENV PYTHONUNBUFFERED=1

# Default command runs tests
CMD ["pytest", "test_search_events.py", "-v", "--tb=short", "--cov=.", "--cov-report=term"]
