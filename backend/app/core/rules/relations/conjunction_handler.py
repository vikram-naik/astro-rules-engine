# app/core/rules/relations/conjunction_handler.py
from datetime import datetime
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

class ConjunctionHandler(IRelationHandler):
    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        planet = (cond.planet or "").lower()
        target = (cond.target or "").lower()
        orb = cond.orb if cond.orb is not None else orb_default
        try:
            lon = provider.longitude(planet, when)
            tlon = provider.longitude(target, when)
        except Exception:
            return False
        return provider.angular_distance(lon, tlon) <= orb
