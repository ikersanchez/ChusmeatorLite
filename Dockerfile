# Build stage for Frontend
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Final stage for Backend and serving Frontend
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy backend project files
COPY backend/pyproject.toml .
# Sync dependencies
RUN uv sync --no-dev

# Copy backend application code
COPY backend/app/ app/

# Copy built frontend assets to backend static directory
COPY --from=frontend-build /frontend/dist/ /app/app/static/

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
