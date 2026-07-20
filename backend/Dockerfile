FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright system deps (only if needed)
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set ownership
RUN mkdir -p uploads logs && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Use gunicorn with uvicorn workers for production robustness
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
