"""In-process background worker that drains the DB-backed job queue.

A daemon thread (started in main.py) polls for `pending` scenarios/sessions,
claims one at a time with `FOR UPDATE SKIP LOCKED` (safe across multiple API
instances), marks it `running`, then runs the slow LLM call outside any request
so nothing times out. Result lands back on the row as `ready` or `error`.

No Redis, no separate worker process — works in the single web service both
locally and on Render's free tier.
"""

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select

from . import services
from .config import settings
from .db import SessionLocal
from .models import JobStatus, Scenario, Session, StudyNote

log = logging.getLogger("worker")
POLL_INTERVAL = 2.0  # seconds between polls when the queue is empty
RECLAIM_INTERVAL = 60.0  # seconds between stale-job sweeps
stop_event = threading.Event()
_last_reclaim = 0.0


def reclaim_stale_jobs() -> None:
    """Drop rows stuck in 'running' beyond the threshold (e.g. the process was
    paused/restarted mid-job). Such scenarios are empty placeholders and such
    sessions never finished judging, so they're discarded rather than retried."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.stale_job_minutes)
    db = SessionLocal()
    try:
        dropped = 0
        for model in (Scenario, Session, StudyNote):
            # Key off when it started running; fall back to created_at for any
            # legacy 'running' rows that predate the running_since column.
            since = func.coalesce(model.running_since, model.created_at)
            res = db.execute(
                delete(model).where(model.status == JobStatus.running, since < cutoff)
            )
            dropped += res.rowcount or 0
        db.commit()
        if dropped:
            log.info("reclaimed %d stale running job(s)", dropped)
    finally:
        db.close()


def _maybe_reclaim() -> None:
    global _last_reclaim
    now = time.monotonic()
    if now - _last_reclaim >= RECLAIM_INTERVAL:
        _last_reclaim = now
        try:
            reclaim_stale_jobs()
        except Exception:
            log.exception("stale-job reclaim failed")


def _claim(db, model) -> "uuid.UUID | None":  # noqa: F821
    """Atomically grab the oldest pending row and mark it running."""
    row = (
        db.execute(
            select(model)
            .where(model.status == JobStatus.pending)
            .order_by(model.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        .scalars()
        .first()
    )
    if row is None:
        db.rollback()  # release locks held by the SELECT
        return None
    row.status = JobStatus.running
    row.running_since = datetime.now(timezone.utc)  # reclaim keys off this, not created_at
    db.commit()  # releases the row lock; other workers can move on
    return row.id


def _run(db, model, row_id, fn) -> None:
    row = db.get(model, row_id)
    try:
        fn(db, row)
    except Exception as exc:  # LLM error, bad JSON, timeout, etc.
        db.rollback()
        detail = getattr(exc, "detail", None) or str(exc)
        row = db.get(model, row_id)
        row.status = JobStatus.error
        row.error = str(detail)[:2000]
        db.commit()
        log.warning("job %s %s failed: %s", model.__tablename__, row_id, detail)


def process_once() -> bool:
    """Process at most one queued job. Returns True if one was handled."""
    db = SessionLocal()
    try:
        sid = _claim(db, Scenario)
        if sid is not None:
            _run(db, Scenario, sid, services.run_scenario_job)
            return True
        jid = _claim(db, Session)
        if jid is not None:
            _run(db, Session, jid, services.run_session_job)
            return True
        nid = _claim(db, StudyNote)
        if nid is not None:
            _run(db, StudyNote, nid, services.run_study_note_job)
            return True
        return False
    finally:
        db.close()


def worker_loop() -> None:
    log.info("job worker started")
    while not stop_event.is_set():
        _maybe_reclaim()
        try:
            handled = process_once()
        except Exception:  # never let the loop die
            log.exception("worker iteration failed")
            handled = False
        if not handled:
            stop_event.wait(POLL_INTERVAL)
