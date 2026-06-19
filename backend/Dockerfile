# ---- Stage 1: build the frontend ----
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: python runtime ----
FROM python:3.12-slim AS runtime
WORKDIR /app

# uv for dependency install
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY backend/pyproject.toml ./
RUN uv pip install --system --no-cache .

COPY backend/ ./
# built frontend served by FastAPI StaticFiles
COPY --from=frontend /frontend/dist ./app/static

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
