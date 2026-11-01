# Production Hardened Dockerfile for Nirikshan Scrutiny Application
FROM python:3.11-slim

# Prevent bytecode generation and unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NIRIKSHAN_ALLOW_EXTERNAL_NETWORK=false \
    NIRIKSHAN_OFFLINE=strict-airgap-local

# Install minimal OS dependencies for cryptography, imaging, and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Non-root security user
RUN useradd -m -u 1001 -s /bin/bash nirikshan

WORKDIR /app

# Install dependencies first for Docker cache optimization
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application code and regulatory rulesets
COPY nirikshan ./nirikshan
COPY rulesets ./rulesets
COPY trust ./trust

# Create storage directories and set ownership
RUN mkdir -p var/quarantine var/parsed_cache var/models trust/keys && \
    chown -R nirikshan:nirikshan /app

USER nirikshan

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "nirikshan.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
