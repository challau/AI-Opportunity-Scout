FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers only if explicitly enabled
# Set PLAYWRIGHT_ENABLED=true in Railway env vars if needed
ARG PLAYWRIGHT_ENABLED=false
RUN if [ "$PLAYWRIGHT_ENABLED" = "true" ]; then \
    playwright install --with-deps chromium; \
    fi

# Copy application code
COPY . .

# Create necessary directories and set ownership
RUN mkdir -p uploads logs && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Use uvicorn for Railway (Railway manages process scaling separately)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
