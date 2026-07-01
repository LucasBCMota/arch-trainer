from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..auth import current_user
from ..db import get_db
from ..models import PatternGap, PatternReview, Session, User
from ..schemas import MarkReviewBody, ReviewItem

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/queue", response_model=list[ReviewItem])
def queue(db: DbSession = Depends(get_db), user: User = Depends(current_user)) -> list[ReviewItem]:
    # Miss counts per pattern from YOUR judged sessions.
    gaps = (
        select(PatternGap.pattern_name.label("pattern_name"), func.count().label("miss"))
        .join(Session, PatternGap.session_id == Session.id)
        .where(Session.user_id == user.id)
        .group_by(PatternGap.pattern_name)
        .subquery()
    )
    # Weakest & most-overdue first: most-missed, then least-recently reviewed (never = first).
    stmt = (
        select(
            gaps.c.pattern_name,
            gaps.c.miss,
            PatternReview.last_reviewed_at,
            PatternReview.review_count,
        )
        .select_from(gaps)
        .join(
            PatternReview,
            (PatternReview.pattern_name == gaps.c.pattern_name)
            & (PatternReview.user_id == user.id),
            isouter=True,
        )
        .order_by(gaps.c.miss.desc(), PatternReview.last_reviewed_at.asc().nulls_first())
    )
    return [
        ReviewItem(
            pattern_name=row[0], miss_count=row[1], last_reviewed_at=row[2], review_count=row[3] or 0
        )
        for row in db.execute(stmt)
    ]


@router.post("/mark")
def mark(
    body: MarkReviewBody, db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> dict:
    pr = db.scalar(
        select(PatternReview).where(
            PatternReview.user_id == user.id, PatternReview.pattern_name == body.pattern
        )
    )
    now = datetime.now(timezone.utc)
    if pr is None:
        db.add(PatternReview(user_id=user.id, pattern_name=body.pattern, last_reviewed_at=now, review_count=1))
    else:
        pr.last_reviewed_at = now
        pr.review_count += 1
    db.commit()
    return {"ok": True}
