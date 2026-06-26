"""Row-level access helpers — keep authZ logic in one place.

Reads: an item is visible to a user iff they own it OR it's public.
Mutations: only the owner may change a row.
Failed checks raise 404 (not 403) so the existence of another user's private row
is never leaked.
"""

from fastapi import HTTPException
from sqlalchemy import or_

from .models import User, Visibility

_NOT_FOUND = HTTPException(status_code=404, detail="Not found")


def visible_filter(model, user: User):
    """SQLAlchemy condition: rows the user owns OR public rows."""
    return or_(model.user_id == user.id, model.visibility == Visibility.public)


def assert_visible(item, user: User):
    if item is None:
        raise _NOT_FOUND
    if item.user_id == user.id or item.visibility == Visibility.public:
        return item
    raise _NOT_FOUND


def assert_owner(item, user: User):
    if item is None or item.user_id != user.id:
        raise _NOT_FOUND
    return item
