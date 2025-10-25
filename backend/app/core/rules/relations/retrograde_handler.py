# app/core/rules/relations/retrograde_handler.py
from datetime import datetime
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

class RetrogradeHandler(IRelationHandler):
    """
    Check if planet is retrograde at 'when'.
    cond.target is ignored. cond.value may be used for 'is not retrograde' if desired.
    """
    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        planet = (cond.planet or "").lower()
        try:
            # This requires provider to implement is_retrograde
            return provider.is_retrograde(planet, when)
        except AttributeError:
            # provider missing retrograde capability => cannot evaluate
            return False
        except Exception:
            return False
