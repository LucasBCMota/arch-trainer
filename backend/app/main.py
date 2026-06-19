from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import models, scenarios, sessions, stats

app = FastAPI(title="Architecture Reasoning Trainer")

app.include_router(scenarios.router)
app.include_router(sessions.router)
app.include_router(stats.router)
app.include_router(models.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# Serve the built frontend (Vite dist copied here in the Docker image). In local
# dev the frontend runs separately via `npm run dev`, so this dir may be absent.
_STATIC = Path(__file__).parent / "static"
if _STATIC.is_dir():
    app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
