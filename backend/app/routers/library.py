import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import exists, select
from sqlalchemy.orm import Session as DbSession

from .. import services
from ..db import get_db
from ..models import Scenario, Session, StudyNote, StudyNoteKind
from ..schemas import (
    PinBody,
    ReferenceArtifactOut,
    StudyCreate,
    StudyEdit,
    StudyImport,
    StudyNoteOut,
)

router = APIRouter(prefix="/api", tags=["library"])


# ---- AI-generated study notes / cheat-sheets ----
@router.post("/study", response_model=StudyNoteOut)
def create_study(payload: StudyCreate, db: DbSession = Depends(get_db)) -> StudyNote:
    return services.generate_study_note(db, payload.topic, StudyNoteKind.deep_dive, payload.model)


@router.post("/cheatsheets", response_model=StudyNoteOut)
def create_cheatsheet(payload: StudyCreate, db: DbSession = Depends(get_db)) -> StudyNote:
    return services.generate_study_note(db, payload.topic, StudyNoteKind.cheat_sheet, payload.model)


# ---- Manual import (paste Markdown made externally — no LLM call) ----
@router.post("/study-notes", response_model=StudyNoteOut)
def import_note(payload: StudyImport, db: DbSession = Depends(get_db)) -> StudyNote:
    note = StudyNote(
        kind=payload.kind,
        topic=payload.topic,
        content_md=payload.content_md,
        model=payload.source or "manual",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ---- Read / edit / pin / delete ----
@router.get("/study-notes", response_model=list[StudyNoteOut])
def list_notes(
    kind: StudyNoteKind | None = None,
    pinned: bool | None = None,
    db: DbSession = Depends(get_db),
) -> list[StudyNote]:
    stmt = select(StudyNote).order_by(StudyNote.created_at.desc())
    if kind is not None:
        stmt = stmt.where(StudyNote.kind == kind)
    if pinned is not None:
        stmt = stmt.where(StudyNote.pinned == pinned)
    return list(db.scalars(stmt).all())


def _get_note(db: DbSession, note_id: uuid.UUID) -> StudyNote:
    note = db.get(StudyNote, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Study note not found")
    return note


@router.get("/study-notes/{note_id}", response_model=StudyNoteOut)
def get_note(note_id: uuid.UUID, db: DbSession = Depends(get_db)) -> StudyNote:
    return _get_note(db, note_id)


@router.put("/study-notes/{note_id}", response_model=StudyNoteOut)
def update_note(note_id: uuid.UUID, payload: StudyEdit, db: DbSession = Depends(get_db)) -> StudyNote:
    note = _get_note(db, note_id)
    if payload.topic is not None:
        note.topic = payload.topic
    if payload.content_md is not None:
        note.content_md = payload.content_md
    db.commit()
    db.refresh(note)
    return note


@router.post("/study-notes/{note_id}/pin", response_model=StudyNoteOut)
def pin_note(note_id: uuid.UUID, payload: PinBody, db: DbSession = Depends(get_db)) -> StudyNote:
    note = _get_note(db, note_id)
    note.pinned = payload.pinned
    db.commit()
    db.refresh(note)
    return note


@router.delete("/study-notes/{note_id}")
def delete_note(note_id: uuid.UUID, db: DbSession = Depends(get_db)) -> dict:
    note = _get_note(db, note_id)
    db.delete(note)
    db.commit()
    return {"ok": True}


# ---- Artifacts: archive of reference designs (answered scenarios only) ----
@router.get("/artifacts/references", response_model=list[ReferenceArtifactOut])
def list_reference_artifacts(db: DbSession = Depends(get_db)) -> list[Scenario]:
    # Only scenarios with at least one session — i.e. already answered. This keeps
    # the no-peek invariant: an unanswered scenario never exposes its reference here.
    answered = exists().where(Session.scenario_id == Scenario.id)
    stmt = select(Scenario).where(answered).order_by(Scenario.created_at.desc())
    return list(db.scalars(stmt).all())
