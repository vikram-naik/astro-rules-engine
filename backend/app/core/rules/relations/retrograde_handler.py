"""
RetrogradeHandler
-----------------
Purpose:
    Determines whether a planet is in retrograde motion at a given time.

Astrological Context:
    In Vedic astrology, a retrograde planet is one that appears to move backward
    across the zodiac from Earth’s perspective. Retrograde motion signifies
    introspection, delays, or revisiting past karmic themes.

Functional Logic:
    - The handler queries the provider’s `is_retrograde(planet, when)` method.
    - It returns True if the planet is retrograde; False otherwise.
    - Gracefully handles provider differences or misconfigurations.

Failure Safety:
    - Missing method (`AttributeError`) → return False.
    - Non-callable method (`TypeError`) → return False.
    - Any unexpected provider error (`Exception`) → return False.

Returns:
    bool → True if retrograde, else False.

Example:
    cond = ConditionRead(
        planet="Mars",
        relation=Relation.is_retrograde,
        target=None
    )
    handler.check(provider, cond, datetime(2025, 1, 1))
"""

from datetime import datetime
from app.core.common.schemas import ConditionRead
from app.core.rules.relations.i_relation import IRelationHandler


class RetrogradeHandler(IRelationHandler):
    """Checks whether a planet is retrograde."""

    def check(self, provider, condition: ConditionRead, when: datetime, orb_default: float) -> bool:
        planet = condition.planet.lower()
        try:
            # Normal path: delegate to provider
            return bool(provider.is_retrograde(planet, when))

        except (AttributeError, TypeError):
            # Missing method or non-callable attribute
            return False
        except Exception:
            # Defensive catch for unexpected provider runtime failure
            return False
