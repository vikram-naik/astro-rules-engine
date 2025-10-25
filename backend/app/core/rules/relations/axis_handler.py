import logging
from datetime import datetime
from app.core.rules.relations.i_relation import IRelationHandler
from app.core.common.schemas import ConditionRead

logger = logging.getLogger("astro.axis")


class AxisHandler(IRelationHandler):
    """Checks if two planets are in opposition (≈ 180° apart) within a given orb."""

    def check(self, provider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        try:
            orb = cond.orb or orb_default
            lon = provider.longitude(cond.planet, when)
            tlon = provider.longitude(cond.target, when)
            ang = provider.angular_distance(lon, tlon)

            logger.debug(
                f"[AxisHandler] planet={cond.planet} target={cond.target} "
                f"lon={lon:.2f}° tlon={tlon:.2f}° ang={ang:.2f}° orb={orb:.2f}"
            )

            # "In Axis" → planets are opposite (≈ 180° apart)
            if abs(ang - 180.0) <= orb:
                logger.debug(f"[AxisHandler] SUCCESS: |{ang:.2f} - 180| <= {orb:.2f}")
                return True

            logger.debug(f"[AxisHandler] FAIL: |{ang:.2f} - 180| > {orb:.2f}")
            return False

        except Exception as e:
            logger.error(f"[AxisHandler] Failed: {e}", exc_info=True)
            return False
