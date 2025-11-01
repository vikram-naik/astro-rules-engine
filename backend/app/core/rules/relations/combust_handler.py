# app/core/rules/relations/combust_handler.py
from datetime import datetime
from app.core.db.models import Condition
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler
from app.core.common.config import settings  # your pydantic settings (if available)



class CombustHandler(IRelationHandler):
    """
    # 🔥 CombustHandler — Planetary Proximity to the Sun

    ## Purpose
    Determines whether a planet is *combust* — positioned so close to the Sun that its influence is considered weakened.
    This relation checks the **angular distance** between the Sun and the target planet.

    ---

    ## 🧭 Functional Logic

    1. **Orb Determination (tolerance in degrees):**
    - Use `cond.orb` if explicitly defined in the rule.
    - Else use `settings.combust_orbs[planet]` if available.
    - Else fallback to `DEFAULT_ORB = 8.0°` (universal threshold).

    2. **Angular Distance Calculation:**
    - Compute the absolute angular separation between the planet and the Sun using:
        ```python
        provider.angular_distance(lon_planet, lon_sun)
        ```
    - The provider ensures correct circular wrap-around (e.g. Sun=359°, Planet=2° → distance=3°).

    3. **Combustion Rule:**
    - A planet is combust if:
        ```python
        distance <= orb_threshold
        ```
    - Otherwise, it is not combust.

    4. **Error Handling:**
    - If the provider fails (missing longitude, runtime error), returns `False`.
    - If settings are misconfigured or inaccessible, falls back safely to the default orb.

    ---

    ## 🪐 Typical Orbs (Traditional Reference)
    | Planet | Orb (°) |
    |---------|----------|
    | Mercury | 12 |
    | Venus   | 10 |
    | Mars    | 8 |
    | Jupiter | 9 |
    | Saturn  | 8 |

    These can be configured in `.env` via `combust_orbs` mapping.

    ---

    ## ✅ Example
    ```python
    # Rule: "Mars is combust by the Sun"
    cond = ConditionRead(planet="Mars", relation=Relation.combust_by_sun)
    CombustHandler().check(provider, cond, datetime.utcnow(), orb_default=8.0)
    Returns True if Mars is within 8° of the Sun.
    """

    DEFAULT_ORB = 8.0  # example fallback; treat as configurable in settings

    def check(self, provider: IAstroProvider, cond: Condition, when: datetime, orb_default: float) -> bool:
        planet = (cond.planet or "").lower()
        orb = cond.orb if cond.orb is not None else None

        # if config available, try to get per-planet orb
        cfg_orb = None
        try:
            cfg_orb = getattr(settings, "astro_combust_orbs", None)  # expect dict-like if present
            if isinstance(cfg_orb, dict):
                cfg_val = cfg_orb.get(planet)
                if cfg_val is not None:
                    cfg_orb = float(cfg_val)
                else:
                    cfg_orb = None
        except Exception as e:
            cfg_orb = None

        use_orb = orb if orb is not None else (cfg_orb if cfg_orb is not None else self.DEFAULT_ORB)

        try:
            lon = provider.longitude(planet, when)
            sun_lon = provider.longitude("sun", when)
        except Exception:
            return False

        return provider.angular_distance(lon, sun_lon) <= use_orb

