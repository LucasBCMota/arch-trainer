import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from .. import services
from ..db import get_db
from ..models import Scenario
from ..schemas import PinBody, ScenarioCreate, ScenarioOut, ScenarioRevealOut

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.post("", response_model=ScenarioOut)
def create_scenario(payload: ScenarioCreate, db: DbSession = Depends(get_db)) -> Scenario:
    # response_model=ScenarioOut has no reference_solution field, so the
    # reference can never reach the frontend before judging.
    return services.generate_scenario(db, payload)


@router.get("/{scenario_id}")
def get_scenario(
    scenario_id: uuid.UUID, reveal: bool = False, db: DbSession = Depends(get_db)
) -> ScenarioOut | ScenarioRevealOut:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if reveal:
        return ScenarioRevealOut.model_validate(scenario)
    return ScenarioOut.model_validate(scenario)


@router.post("/{scenario_id}/pin", response_model=ScenarioOut)
def pin_scenario(
    scenario_id: uuid.UUID, payload: PinBody, db: DbSession = Depends(get_db)
) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario.pinned = payload.pinned
    db.commit()
    db.refresh(scenario)
    return scenario
