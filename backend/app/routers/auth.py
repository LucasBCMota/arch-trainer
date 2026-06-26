from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm.attributes import flag_modified

from .. import auth
from ..config import settings
from ..db import get_db
from ..models import User
from ..schemas import FavoriteModelsBody

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


def _user_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.display_name,
        "picture": user.picture,
        "is_owner": auth.is_owner(user),
        "favorite_models": user.favorite_models or [],
    }


@router.get("/me")
def me(user: User = Depends(auth.current_user)) -> dict:
    return {"authenticated": True, "user": _user_dict(user)}


@router.put("/me/favorite-models")
def set_favorite_models(
    body: FavoriteModelsBody,
    db: DbSession = Depends(get_db),
    user: User = Depends(auth.current_user),
) -> dict:
    # de-dupe, drop blanks, preserve order; cap to keep it tidy.
    seen, cleaned = set(), []
    for m in body.models:
        m = (m or "").strip()
        if m and m not in seen:
            seen.add(m)
            cleaned.append(m)
    user.favorite_models = cleaned[:20]
    flag_modified(user, "favorite_models")  # JSONB in-place reassignment
    db.commit()
    db.refresh(user)
    return {"favorite_models": user.favorite_models}
