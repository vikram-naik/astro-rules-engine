from fastapi import APIRouter
from app.core.db.enums import Planet, Relation, OutcomeEffect, Sign, enum_to_ref

router = APIRouter(prefix="/api/reference", tags=["reference"])

@router.get("/")
def get_reference_data():
    """Returns all reference data for rule editor UI."""
    return {
        "planets": enum_to_ref(Planet),
        "signs": enum_to_ref(Sign),
        "relations": [
            {
                "key": r.name,
                "label": r.value.label,
                "target_source": r.value.target_source,
                "has_orb": r.value.has_orb,
                "has_value": r.value.has_value,
                "requires_target": r.value.requires_target,
                "requires_planet": r.value.requires_planet,
                "i18n": f"relation.{r.name}"
            }
            for r in Relation
        ],
        "effects": enum_to_ref(OutcomeEffect),
    }

@router.get("/signs")
def get_signs():
    """Returns all zodiac signs for dropdown population."""
    return enum_to_ref(Sign)