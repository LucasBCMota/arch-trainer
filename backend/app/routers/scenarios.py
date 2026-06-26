import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from .. import services
from ..access import assert_owner, assert_visible
from ..auth import current_user, require_owner
from ..db import get_db
from ..models import Scenario, User
from ..schemas import (
    PinBody,
    ScenarioCreate,
    ScenarioOut,
    ScenarioRevealOut,
    VisibilityBody,
)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.post("", response_model=ScenarioOut)
def create_scenario(
    payload: ScenarioCreate,
    db: DbSession = Depends(get_db),
    owner: User = Depends(require_owner),  # generation spends the server's keys
) -> Scenario:
    # response_model=ScenarioOut has no reference_solution field, so the
    # reference can never reach the frontend before judging.
    return services.generate_scenario(db, payload, owner)


@router.get("/{scenario_id}")
def get_scenario(
    scenario_id: uuid.UUID,
    reveal: bool = False,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> ScenarioOut | ScenarioRevealOut:
    scenario = assert_visible(db.get(Scenario, scenario_id), user)
    # Only the owner may unhide the reference (the no-peek invariant).
    if reveal and scenario.user_id == user.id:
        return ScenarioRevealOut.model_validate(scenario)
    return ScenarioOut.model_validate(scenario)


@router.post("/{scenario_id}/pin", response_model=ScenarioOut)
def pin_scenario(
    scenario_id: uuid.UUID,
    payload: PinBody,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> Scenario:
    scenario = assert_owner(db.get(Scenario, scenario_id), user)
    scenario.pinned = payload.pinned
    db.commit()
    db.refresh(scenario)
    return scenario


@router.post("/{scenario_id}/visibility", response_model=ScenarioOut)
def set_visibility(
    scenario_id: uuid.UUID,
    payload: VisibilityBody,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user),
) -> Scenario:
    scenario = assert_owner(db.get(Scenario, scenario_id), user)
    scenario.visibility = payload.visibility
    db.commit()
    db.refresh(scenario)
    return scenario
