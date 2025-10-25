# app/core/rules/relations/house_relative_handler.py
from datetime import datetime
import logging
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

# TODO: Important: HouseRelativeHandler uses a simple house-centre approach; 
# if you have a different house system (e.g., Placidus, Equal, Whole sign), 
# we should extend the provider API to return house cusps and use that instead.

logger = logging.getLogger("astro.house_relative")

class HouseRelativeHandler(IRelationHandler):
    """
    Check if planet is in a house relative to a reference planet.
    This uses angular distance relative to reference planet and optionally cond.value
    may specify a house offset (e.g., 4 for 4th from reference).
    """
    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        try:
            orb = cond.orb or orb_default
            target_house = int(cond.value)

            ref_lon = provider.longitude(cond.target, when)
            planet_lon = provider.longitude(cond.planet, when)

            rel_angle = (planet_lon - ref_lon) % 360
            rel_house = int((rel_angle + 1e-6) // 30) + 1  # small epsilon for precision

            logger.debug(
                f"[HouseRelativeHandler] planet={cond.planet}({planet_lon:.2f}°) "
                f"from {cond.target}({ref_lon:.2f}°) -> rel_angle={rel_angle:.2f}° -> rel_house={rel_house}"
            )

            if rel_house == target_house:
                logger.debug(f"[HouseRelativeHandler] SUCCESS: {cond.planet} in house {rel_house} from {cond.target}")
                return True

            logger.debug(f"[HouseRelativeHandler] FAIL: expected={target_house}, got={rel_house}")
            return False

        except Exception as e:
            logger.error(f"[HouseRelativeHandler] Failed for {cond.planet}-{cond.target}: {e}", exc_info=True)
            return False