# app/core/rules/relations/sign_handler.py
from datetime import datetime
from typing import Optional

from app.core.common.schemas import ConditionRead
from app.core.db.enums import Sign
from app.core.rules.relations.i_relation import IRelationHandler
from app.core.astro.interfaces.i_astro_provider import IAstroProvider

class SignHandler(IRelationHandler):
    """
    Checks if a planet is located in a specified zodiac sign.
    Uses the canonical Sign enum for matching but enforces the correct zodiacal order.
    """

    # Explicit zodiac order mapped to enum members
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
        """
        Resolve numeric or name-based target into sign index (0–11).
        """
        target_raw = (target_raw or "").strip()
        if target_raw.isdigit():
            idx = int(target_raw)
            if 0 <= idx <= 11:
                return idx
            return None

        # Match by enum .name or .value
        for idx, sign in enumerate(self.ZODIAC_ORDER):
            if sign.name.lower() == target_raw.lower() or sign.value.lower() == target_raw.lower():
                return idx

        return None

    def check(
        self,
        provider: IAstroProvider,
        condition: ConditionRead,
        when: datetime,
        orb_default: float,
    ) -> bool:
        planet = (condition.planet or "").lower()
        target_raw = (condition.target or "").strip()

        try:
            lon = provider.longitude(planet, when)
        except Exception:
            return False
        
        # 🔧 Normalize and compute sign index correctly
        lon = lon % 360.0
        sign_index = int(lon // 30.0)

        target_index = self._resolve_target_index(target_raw)
        # Debug (optional)
        # print(f"sign_index={sign_index}, target_index={target_index}, lon={lon}")

        if target_index is None:
            return False

        return sign_index == target_index
