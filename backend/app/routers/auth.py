from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DbSession

from .. import auth
from ..config import settings
from ..db import get_db

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/auth/login")
async def login(request: Request, connection: str | None = None):
    if not settings.auth0_configured:
        # Dev mode: nothing to redirect to — current_user already returns the dev owner.
        return RedirectResponse(url="/")
    redirect_uri = f"{settings.app_base_url}/api/auth/callback"
    kwargs = {"connection": connection} if connection else {}
    return await auth.oauth.auth0.authorize_redirect(request, redirect_uri, **kwargs)


@router.get("/auth/callback")
async def callback(request: Request, db: DbSession = Depends(get_db)):
    if not settings.auth0_configured:
        return RedirectResponse(url="/")
    try:
        token = await auth.oauth.auth0.authorize_access_token(request)
    except Exception as exc:  # invalid state, denied consent, etc.
        raise HTTPException(status_code=401, detail=f"Login failed: {exc}") from exc

    info = token.get("userinfo") or {}
    sub = info.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Auth0 returned no subject")
    user = auth.upsert_user(
        db, sub=sub, email=info.get("email", ""), name=info.get("name"), picture=info.get("picture")
    )
    # Store ONLY the local user id — never the OAuth tokens.
    request.session["user_id"] = str(user.id)
    return RedirectResponse(url="/")


@router.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    if not settings.auth0_configured:
        return RedirectResponse(url="/")
    params = urlencode({"client_id": settings.auth0_client_id, "returnTo": settings.app_base_url})
    return RedirectResponse(url=f"https://{settings.auth0_domain}/v2/logout?{params}")


@router.get("/me")
def me(user=Depends(auth.current_user)) -> dict:
    return {
        "authenticated": True,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.display_name,
            "picture": user.picture,
            "is_owner": auth.is_owner(user),
        },
    }
