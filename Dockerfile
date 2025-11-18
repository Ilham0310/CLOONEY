FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for capture scripts)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Create database directory
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

# Initialize database and start server
CMD ["sh", "-c", "cd fastapi_app && python -c 'from database import init_db; init_db()' && uvicorn main:app --host 0.0.0.0 --port 8000"]

