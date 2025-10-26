# app/core/rules/relations/conjunction_handler.py
from datetime import datetime
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

class ConjunctionHandler(IRelationHandler):

    
    """
    ConjunctionHandler
    ------------------
    Astrological Meaning:
        In astrology, a *conjunction* occurs when two planets are close together
        in the zodiac — typically within a few degrees. This proximity indicates
        a blending or unification of their energies.

    Functional Logic:
        This handler evaluates whether two celestial bodies are in conjunction
        based on their *angular separation*.

    Evaluation Rules:
        1. The angular distance between the two planets (0°–180°) is computed using:
            provider.angular_distance(lon1, lon2)
        2. If this distance is less than or equal to the allowable orb (in degrees),
        the condition returns True (indicating conjunction).
        3. Otherwise, it returns False.

        Orb Rules:
            - The `orb` parameter can be explicitly defined in the condition.
            - If omitted, a default value (`orb_default`) is applied.
        Error Handling:
            - Any failure in obtaining planet longitudes (e.g., invalid planet names)
            results in a safe `False` return rather than an exception.

    Example:
        # Venus and Sun are within 5° -> conjunction
        cond = ConditionRead(planet="venus", target="sun", relation=Relation.conjunct_with, orb=5)
        handler.check(provider, cond, datetime(2025, 1, 1), orb_default=3.0)
    """



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
