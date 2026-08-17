FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiling psycopg2/asyncpg if any, plus curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . .

EXPOSE 8000

# Default command runs Uvicorn dev server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
