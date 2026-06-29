import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import exists, select, update
from sqlalchemy.orm import Session as DbSession

from .. import services
from ..access import assert_owner, assert_visible
from ..auth import current_user, require_owner
from ..db import get_db
from ..models import JobStatus, Scenario, Session, StudyNote, StudyNoteKind, User, Visibility
from ..schemas import (
    PinBody,
    ReferenceArtifactOut,
    StudyCreate,
    StudyEdit,
    StudyImport,
    StudyNoteOut,
    VisibilityBody,
)

router = APIRouter(prefix="/api", tags=["library"])


# ---- AI-generated study notes / cheat-sheets (owner-only: spends keys) ----
# Enqueued as background jobs; poll GET /api/study-notes/{id} until ready.
@router.post("/study", response_model=StudyNoteOut)
def create_study(
    payload: StudyCreate, db: DbSession = Depends(get_db), owner: User = Depends(require_owner)
) -> StudyNote:
    return services.enqueue_study_note(db, payload.topic, StudyNoteKind.deep_dive, payload.model, owner)


@router.post("/cheatsheets", response_model=StudyNoteOut)
def create_cheatsheet(
    payload: StudyCreate, db: DbSession = Depends(get_db), owner: User = Depends(require_owner)
) -> StudyNote:
    return services.enqueue_study_note(db, payload.topic, StudyNoteKind.cheat_sheet, payload.model, owner)


# ---- Manual import (any user — no LLM call, no token cost) ----
@router.post("/study-notes", response_model=StudyNoteOut)
def import_note(
    payload: StudyImport, db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> StudyNote:
    note = StudyNote(
        kind=payload.kind,
        topic=payload.topic,
        content_md=payload.content_md,
        model=payload.source or "manual",
        user_id=user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ---- Read / edit / pin / visibility / delete (own library) ----
@router.get("/study-notes", response_model=list[StudyNoteOut])
def list_notes(
    kind: StudyNoteKind | None = None,
    pinned: bool | None = None,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> list[StudyNote]:
    stmt = (
        select(StudyNote)
        # your own *finished* library — pending/errored generations are excluded
        .where(StudyNote.user_id == user.id, StudyNote.status == JobStatus.ready)
        .order_by(StudyNote.created_at.desc())
    )
    if kind is not None:
        stmt = stmt.where(StudyNote.kind == kind)
    if pinned is not None:
        stmt = stmt.where(StudyNote.pinned == pinned)
    return list(db.scalars(stmt).all())


@router.get("/study-notes/{note_id}", response_model=StudyNoteOut)
def get_note(
    note_id: uuid.UUID, db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> StudyNoteOut:
    note = assert_visible(db.get(StudyNote, note_id), user)
    return _note_out(note, user)


@router.put("/study-notes/{note_id}", response_model=StudyNoteOut)
def update_note(
    note_id: uuid.UUID,
    payload: StudyEdit,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> StudyNote:
    note = assert_owner(db.get(StudyNote, note_id), user)
    if payload.topic is not None:
        note.topic = payload.topic
    if payload.content_md is not None:
        note.content_md = payload.content_md
    db.commit()
    db.refresh(note)
    return note


@router.post("/study-notes/{note_id}/pin", response_model=StudyNoteOut)
def pin_note(
    note_id: uuid.UUID,
    payload: PinBody,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> StudyNote:
    note = assert_owner(db.get(StudyNote, note_id), user)
    note.pinned = payload.pinned
    db.commit()
    db.refresh(note)
    return note


@router.post("/study-notes/{note_id}/visibility", response_model=StudyNoteOut)
def set_note_visibility(
    note_id: uuid.UUID,
    payload: VisibilityBody,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> StudyNote:
    note = assert_owner(db.get(StudyNote, note_id), user)
    note.visibility = payload.visibility
    db.commit()
    db.refresh(note)
    return note


@router.delete("/study-notes/{note_id}")
def delete_note(
    note_id: uuid.UUID, db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> dict:
    note = assert_owner(db.get(StudyNote, note_id), user)
    db.delete(note)
    db.commit()
    return {"ok": True}


# ---- Artifacts: your archive of reference designs (answered scenarios only) ----
@router.get("/artifacts/references", response_model=list[ReferenceArtifactOut])
def list_reference_artifacts(
    db: DbSession = Depends(get_db), user: User = Depends(current_user)
) -> list[Scenario]:
    answered = exists().where(Session.scenario_id == Scenario.id)
    stmt = (
        select(Scenario)
        .where(answered, Scenario.user_id == user.id)
        .order_by(Scenario.created_at.desc())
    )
    return list(db.scalars(stmt).all())


# ---- Public browse (any logged-in user; only public rows; author name only) ----
def _note_out(note: StudyNote, user: User) -> StudyNoteOut:
    out = StudyNoteOut.model_validate(note)
    if note.user_id != user.id and note.user is not None:
        out.author = note.user.display_name
    return out


@router.get("/public/study-notes", response_model=list[StudyNoteOut])
def public_notes(db: DbSession = Depends(get_db), _: User = Depends(current_user)) -> list[StudyNoteOut]:
    stmt = (
        select(StudyNote)
        .where(StudyNote.visibility == Visibility.public, StudyNote.status == JobStatus.ready)
        .order_by(StudyNote.created_at.desc())
    )
    notes = db.scalars(stmt).all()
    out = []
    for n in notes:
        o = StudyNoteOut.model_validate(n)
        o.author = n.user.display_name if n.user else None
        out.append(o)
    return out


@router.get("/public/references", response_model=list[ReferenceArtifactOut])
def public_references(
    db: DbSession = Depends(get_db), _: User = Depends(current_user)
) -> list[ReferenceArtifactOut]:
    answered = exists().where(Session.scenario_id == Scenario.id)
    stmt = (
        select(Scenario)
        .where(answered, Scenario.visibility == Visibility.public)
        .order_by(Scenario.created_at.desc())
    )
    out = []
    for sc in db.scalars(stmt).all():
        o = ReferenceArtifactOut.model_validate(sc)
        o.author = sc.user.display_name if sc.user else None
        out.append(o)
    return out


# ---- Owner-only: claim pre-auth (NULL-owner) rows ----
@router.post("/admin/claim-legacy")
def claim_legacy(db: DbSession = Depends(get_db), owner: User = Depends(require_owner)) -> dict:
    counts = {}
    for model in (Scenario, Session, StudyNote):
        res = db.execute(
            update(model).where(model.user_id.is_(None)).values(user_id=owner.id)
        )
        counts[model.__tablename__] = res.rowcount
    db.commit()
    return {"claimed": counts}
