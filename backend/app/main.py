import threading
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import worker
from .auth import current_user
from .config import settings
from .routers import auth, interview, library, models, review, scenarios, sessions, stats

app = FastAPI(title="Architecture Reasoning Trainer")


@app.on_event("startup")
def _start_worker() -> None:
    # In-process background worker drains the LLM job queue (see worker.py).
    if settings.run_worker:
        threading.Thread(target=worker.worker_loop, daemon=True, name="job-worker").start()

# Signs the httponly session cookie that holds the logged-in user id.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.session_https_only,
)

# Open routes: auth (login/callback/logout/me) + health.
app.include_router(auth.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# Everything else requires a logged-in user (per-row ownership is enforced inside
# each handler via the injected current_user).
_protected = [Depends(current_user)]
app.include_router(scenarios.router, dependencies=_protected)
app.include_router(sessions.router, dependencies=_protected)
app.include_router(stats.router, dependencies=_protected)
app.include_router(models.router, dependencies=_protected)
app.include_router(library.router, dependencies=_protected)
app.include_router(review.router, dependencies=_protected)
app.include_router(interview.router, dependencies=_protected)


# Serve the built frontend (Vite dist copied here in the Docker image). In local
# dev the frontend runs separately via `npm run dev`, so this dir may be absent.
_STATIC = Path(__file__).parent / "static"
if _STATIC.is_dir():
    app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
