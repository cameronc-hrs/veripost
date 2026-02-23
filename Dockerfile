FROM python:3.11-slim

# Install system dependencies for asyncpg (PostgreSQL client library)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip for reliable dependency resolution
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy dependency manifest first for layer caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy Alembic migration config and scripts
COPY alembic.ini .
COPY alembic/ alembic/

# Copy application code
COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
