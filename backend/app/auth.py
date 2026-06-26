"""Authentication & authorization.

Auth0 server-side BFF: the backend runs the OIDC code flow (Authlib), reads
userinfo once, and stores only the local `user_id` in the signed httponly session
cookie. OAuth tokens are never persisted or exposed to the browser.

Two authZ tiers:
  - current_user : any logged-in user (AuthN).
  - require_owner: user whose email is in OWNER_EMAILS — the only ones allowed to
    spend the server's LLM keys. `can_spend()` is the seam for future BYO-key.

If Auth0 is not configured, a local dev-owner is auto-logged-in so the app is
usable without a tenant.
"""

import uuid

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from .config import settings
from .db import get_db
from .models import User

DEV_SUB = "dev|local"
DEV_EMAIL = "dev@local"

oauth = OAuth()
if settings.auth0_configured:
    oauth.register(
        name="auth0",
        client_id=settings.auth0_client_id,
        client_secret=settings.auth0_client_secret,
        server_metadata_url=f"https://{settings.auth0_domain}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )


def is_owner(user: User) -> bool:
    # If no allowlist is configured, treat every user as an owner (single-user /
    # dev convenience). Set OWNER_EMAILS in production to lock spending down.
    owners = settings.owner_email_set
    if not owners:
        return True
    return (user.email or "").lower() in owners


def can_spend(user: User) -> bool:
    """Whether this user may spend the server's LLM keys. Today == owner.
    Future bring-your-own-key check slots in here."""
    return is_owner(user)


def upsert_user(db: DbSession, sub: str, email: str, name: str | None, picture: str | None) -> User:
    user = db.scalar(select(User).where(User.sub == sub))
    if user is None:
        user = User(sub=sub, email=email, name=name, picture=picture)
        db.add(user)
    else:
        user.email, user.name, user.picture = email, name, picture
    db.commit()
    db.refresh(user)
    return user


def _dev_user(db: DbSession) -> User:
    user = db.scalar(select(User).where(User.sub == DEV_SUB))
    if user is None:
        user = User(sub=DEV_SUB, email=DEV_EMAIL, name="Dev Owner")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def current_user(request: Request, db: DbSession = Depends(get_db)) -> User:
    # Local fallback: no Auth0 -> always act as the dev owner.
    if not settings.auth0_configured:
        return _dev_user(db)

    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user = db.get(User, uuid.UUID(uid))
    except ValueError:
        user = None
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_owner(user: User = Depends(current_user)) -> User:
    if not can_spend(user):
        raise HTTPException(
            status_code=403,
            detail="Only an owner can run AI generation (it spends the server's LLM keys).",
        )
    return user
