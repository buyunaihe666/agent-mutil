FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip instead of COPY --from=ghcr.io
RUN pip install uv

WORKDIR /app

# Copy dependencies first for layer caching
COPY pyproject.toml uv.lock* ./

# Use --offline mode: resolve dependencies during build but cache them
# Pre-download all packages to avoid needing PyPI at runtime
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
