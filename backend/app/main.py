from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth import require_auth
from .auth import router as auth_router
from .config import settings
from .routers import models, scenarios, sessions, stats

app = FastAPI(title="Architecture Reasoning Trainer")

# Signs the session cookie used by the password gate.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=False,  # also works over http for local dev
)

# Open routes.
app.include_router(auth_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# Token-spending / data routes — gated behind the shared password.
_protected = [Depends(require_auth)]
app.include_router(scenarios.router, dependencies=_protected)
app.include_router(sessions.router, dependencies=_protected)
app.include_router(stats.router, dependencies=_protected)
app.include_router(models.router, dependencies=_protected)


# Serve the built frontend (Vite dist copied here in the Docker image). In local
# dev the frontend runs separately via `npm run dev`, so this dir may be absent.
_STATIC = Path(__file__).parent / "static"
if _STATIC.is_dir():
    app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
