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
    cond = Condition(
        planet="Mars",
        relation=Relation.is_retrograde,
        target=None
    )
    handler.check(provider, cond, datetime(2025, 1, 1))
"""

from datetime import datetime
import logging
from app.core.db.models import Condition
from app.core.rules.relations.i_relation import IRelationHandler

logger = logging.getLogger("relation.is_retrograde")

class RetrogradeHandler(IRelationHandler):
    """Checks whether a planet is retrograde."""

    def check(self, provider, condition: Condition, when: datetime, orb_default: float) -> bool:
        planet = condition.planet.lower()
        try:
            logger.debug(f"planet:{planet} when:{when}")
            # Normal path: delegate to provider
            result = provider.is_retrograde(planet, when)
            logger.debug(f"result:{result}")
            # return bool(provider.is_retrograde(planet, when))
            return result
        except (AttributeError, TypeError) as e:
            logger.exception(f"1. Exception encountered :: {e}", exc_info=True)
            # Missing method or non-callable attribute
            return False
        except Exception as e:
            logger.exception(f"2. Unepected exc encountered :: {e}", exc_info=True)
            # Defensive catch for unexpected provider runtime failure
            return False
