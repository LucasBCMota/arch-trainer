"""Single shared-password gate for the token-spending API.

If APP_PASSWORD is unset, auth is disabled (local dev). When set, clients must
POST /api/login with it; that stamps a signed session cookie, and protected
routes check it via the require_auth dependency.
"""

import secrets

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .config import settings

router = APIRouter(prefix="/api", tags=["auth"])


def auth_enabled() -> bool:
    return bool(settings.app_password)


def require_auth(request: Request) -> None:
    """Dependency: 401 unless authenticated (or auth is disabled)."""
    if not auth_enabled():
        return
    if not request.session.get("auth"):
        raise HTTPException(status_code=401, detail="Authentication required")


class LoginBody(BaseModel):
    password: str


@router.get("/me")
def me(request: Request) -> dict:
    return {
        "auth_required": auth_enabled(),
        "authenticated": (not auth_enabled()) or bool(request.session.get("auth")),
    }


@router.post("/login")
def login(body: LoginBody, request: Request) -> dict:
    if not auth_enabled():
        return {"ok": True}  # nothing to check
    if not secrets.compare_digest(body.password, settings.app_password or ""):
        raise HTTPException(status_code=401, detail="Wrong password")
    request.session["auth"] = True
    return {"ok": True}


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}
