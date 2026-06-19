from fastapi import APIRouter

from .. import llm
from ..config import settings
from ..schemas import ModelsInfo

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=ModelsInfo)
def list_models() -> ModelsInfo:
    available = llm.available_providers()
    return ModelsInfo(
        current=settings.llm_model,
        available=available,
        suggested={p: llm.SUGGESTED_MODELS[p] for p in available},
    )
