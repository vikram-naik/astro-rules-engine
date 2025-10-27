from fastapi import APIRouter
from app.core.db.enums import Planet, Relation, OutcomeEffect, Sign

router = APIRouter(prefix="/api/reference", tags=["reference"])

@router.get("/")
def get_reference_data():
    """Returns all reference data for rule editor UI."""
    return {
        "planets": [{"key": p.name, "label": p.value} for p in Planet],
        "signs": [{"key": s.name, "label": s.value} for s in Sign],
        "relations": [
            {
                "key": r.name,
                "label": r.value.label,
                "target_source": r.value.target_source,
                "has_orb": r.value.has_orb,
                "has_value": r.value.has_value,
                "requires_target": r.value.requires_target,
                "requires_planet": r.value.requires_planet,
            }
            for r in Relation
        ],
        "effects": [{"key": e.name, "label": e.value} for e in OutcomeEffect]
    }

@router.get("/signs")
def get_signs():
    """Returns all zodiac signs for dropdown population."""
    return [{"key": s.name, "label": s.value} for s in Sign]
