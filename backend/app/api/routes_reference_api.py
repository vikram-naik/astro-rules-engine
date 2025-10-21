from fastapi import APIRouter
from app.core.common.enums import Planet, Relation, OutcomeEffect

router = APIRouter(prefix="/api/reference", tags=["reference"])

@router.get("/")
def get_reference_data():
    return {
        "planets": [{"key": p.name, "label": p.value} for p in Planet],
        "relations": [{"key": r.name, "label": r.value} for r in Relation],
        "effects": [{"key": e.name, "label": e.value} for e in OutcomeEffect]
    }

