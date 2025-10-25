# app/core/rules/relations/combust_handler.py
from datetime import datetime
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler
from app.core.common.config import settings  # your pydantic settings (if available)


class CombustHandler(IRelationHandler):
    """
    Check if a planet is combust by the Sun.
    Uses cond.orb if provided, else reads per-planet orb from settings.combust_orbs or uses a fallback default.
    """

    DEFAULT_ORB = 8.0  # example fallback; treat as configurable in settings

    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        planet = (cond.planet or "").lower()
        orb = cond.orb if cond.orb is not None else None

        # if config available, try to get per-planet orb
        cfg_orb = None
        try:
            cfg_orb = getattr(settings, "combust_orbs", None)  # expect dict-like if present
            if isinstance(cfg_orb, dict):
                cfg_val = cfg_orb.get(planet)
                if cfg_val is not None:
                    cfg_orb = float(cfg_val)
                else:
                    cfg_orb = None
        except Exception:
            cfg_orb = None

        use_orb = orb if orb is not None else (cfg_orb if cfg_orb is not None else self.DEFAULT_ORB)

        try:
            lon = provider.longitude(planet, when)
            sun_lon = provider.longitude("sun", when)
        except Exception:
            return False

        return provider.angular_distance(lon, sun_lon) <= use_orb
