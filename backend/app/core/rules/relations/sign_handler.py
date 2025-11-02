"""
SignHandler
------------
Purpose:
    Determines whether a planet lies within a given zodiac sign at a given time.

Astrological Context:
    The zodiac is divided into 12 signs of 30° each, starting at 0° Aries.
    Each sign occupies a 30° range:
        0°–29.999°  → Aries (index 0)
        30°–59.999° → Taurus (index 1)
        ...
        330°–359.999° → Pisces (index 11)

Functional Logic:
    1. Query the planet’s longitude via the provider.
    2. Normalize longitude (mod 360°) and compute sign index = floor(longitude / 30).
    3. Resolve the target (sign name or numeric string) to its canonical index.
    4. Compare both indices.

Failure Safety:
    - Returns False if:
        - Provider raises any error.
        - Target cannot be resolved.
        - Longitude invalid or out of range.

Example:
    cond = Condition(
        planet="Sun",
        relation=Relation.in_sign,
        target="Leo"
    )
    handler.check(provider, cond, datetime(2025, 1, 1))
"""

from datetime import datetime
from typing import Optional

from app.core.db.enums import Sign
from app.core.db.models import Condition
from app.core.rules.relations.i_relation import IRelationHandler
from app.core.astro.interfaces.i_astro_provider import IAstroProvider


class SignHandler(IRelationHandler):
    """Checks if a planet is located in a specified zodiac sign."""

    ZODIAC_ORDER = [
        Sign.aries,
        Sign.taurus,
        Sign.gemini,
        Sign.cancer,
        Sign.leo,
        Sign.virgo,
        Sign.libra,
        Sign.scorpio,
        Sign.sagittarius,
        Sign.capricorn,
        Sign.aquarius,
        Sign.pisces,
    ]

    def _resolve_target_index(self, target_raw: str) -> Optional[int]:
        """Resolve numeric or name-based target into sign index (0–11)."""
        target_raw = (target_raw or "").strip()
        if not target_raw:
            return None

        if target_raw.isdigit():
            idx = int(target_raw)
            return idx if 0 <= idx <= 11 else None

        # Match by enum .name or .value (case-insensitive)
        for idx, sign in enumerate(self.ZODIAC_ORDER):
            if (
                sign.name.lower() == target_raw.lower()
                or sign.value.lower() == target_raw.lower()
            ):
                return idx
        return None

    def check(
        self,
        provider: IAstroProvider,
        condition: Condition,
        when: datetime,
        orb_default: float,
    ) -> bool:
        planet = (condition.planet or "").lower()
        target_raw = (condition.target or "").strip()

        try:
            lon = provider.longitude(planet, when)
        except Exception:
            return False

        lon = lon % 360.0
        sign_index = int(lon // 30.0)
        target_index = self._resolve_target_index(target_raw)

        if target_index is None:
            return False

        return sign_index == target_index
