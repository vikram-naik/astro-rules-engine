# app/core/rules/relations/nakshatra_handler.py
from datetime import datetime
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

class NakshatraOwnedHandler(IRelationHandler):
    """
    Check if planet is in a nakshatra owned by the target planet name.
    cond.target expected to be the owner planet name (case-insensitive).
    """
    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        planet = (cond.planet or "").lower()
        owner_target = (cond.target or "").lower()
        try:
            lon = provider.longitude(planet, when)
            nk = provider.nakshatra_index(lon)
            owner = provider.nakshatra_owner(nk)
        except Exception:
            return False
        return owner.lower() == owner_target
