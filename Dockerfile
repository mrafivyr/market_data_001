# --- Base Stage: Shared runtime dependencies ---
FROM python:3.14-slim AS base
WORKDIR /app

# Ensure curl is available if uv needs to fetch assets (optional but safer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy configuration and lockfiles
COPY pyproject.toml uv.lock ./

# Sync only production dependencies
RUN uv sync --frozen --no-dev

# Copy shared modules
COPY src/config.py src/database.py ./src/


# --- Stage 1: Test Image ---
FROM base AS tester
# Re-sync to include testing/dev dependencies (like pytest)
RUN uv sync --frozen
# Copy all source files and test files needed for execution
COPY src/ ./src/
COPY tests/ ./tests/
COPY conftest.py* .git* ./ 
CMD ["uv", "run", "pytest"]


# --- Stage 2: Ingestion Image ---
FROM base AS ingestion
COPY src/ingestion.py ./src/
CMD ["uv", "run", "python", "src/ingestion.py"]


# --- Stage 3: FastAPI Server Image ---
FROM base AS server
COPY src/server.py ./src/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
