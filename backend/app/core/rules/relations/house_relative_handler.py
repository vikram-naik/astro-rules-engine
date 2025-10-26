"""
HouseRelativeHandler
--------------------

Computes the relative house position of one planet with respect to another
based purely on ecliptic longitudes.

### Functional Overview

Each astrological house spans **30°** on the zodiac circle.
Given two longitudes:

- **Reference planet** (`target`) acts as the first house cusp (0° offset).
- **Subject planet** (`planet`) determines how many 30° segments away it lies.

The result is an integer house number from **1 → 12**:

| Relative Angular Range (°) | House Number | Symbolic Meaning          |
|----------------------------:|:-------------|:--------------------------|
| 0° ≤ Δ < 30°               | 1 | Same house / conjunctional zone |
| 30° ≤ Δ < 60°              | 2 | Next house (growth, material gain) |
| 60° ≤ Δ < 90°              | 3 | Siblings, effort, short journeys |
| 90° ≤ Δ < 120°             | 4 | Home, emotions, foundations |
| 120° ≤ Δ < 150°            | 5 | Creativity, intelligence, progeny |
| 150° ≤ Δ < 180°            | 6 | Work, health, service |
| 180° ≤ Δ < 210°            | 7 | Partnerships, marriage, contracts |
| 210° ≤ Δ < 240°            | 8 | Transformation, occult, longevity |
| 240° ≤ Δ < 270°            | 9 | Dharma, travel, fortune |
| 270° ≤ Δ < 300°            | 10 | Career, reputation, public life |
| 300° ≤ Δ < 330°            | 11 | Gains, desires, networks |
| 330° ≤ Δ ≤ 360°            | 12 | Loss, introspection, liberation |

### Numerical Logic

1. Compute the **difference** between planet and reference longitudes.
2. Normalize within `[0, 360)` by modulo operation to handle wrap-arounds.
3. Divide by **30° per house** → `rel_house = floor(diff / 30°) + 1`.
4. If `rel_house > 12` → clamp to **12** (ensuring cyclical closure).
5. If `diff == 360°` → explicitly assign **12th house**.
6. Return `True` only when `rel_house == cond.value`.

### Error Handling

- All angle arithmetic uses `decimal.Decimal` for stable precision up to 4 decimal places.
- Any internal exception (e.g., quantization failure, invalid longitude) is logged
  and gracefully results in `False`.

### Testing Coverage

The following behavioral scenarios are fully tested:
- ✅ Standard house alignment (1st, 4th, 7th)
- ✅ 30° boundary transitions and inclusivity
- ✅ Wrap-around across 0° / 360°
- ✅ rel_angle == 360° → 12th house
- ✅ rel_house > 12 → clamp to 12
- ✅ Negative (non-matching) condition branch
- ✅ Internal exception handling

This ensures deterministic, side-effect-free classification of relative planetary houses
for all possible input conditions.
"""

import logging
from datetime import datetime
from decimal import Decimal, getcontext
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

logger = logging.getLogger("astro.house_relative")
getcontext().prec = 8


class HouseRelativeHandler(IRelationHandler):
    """
    ---------------------------------------------------------------------------
    🪐 HOUSE RELATIVE HANDLER
    ---------------------------------------------------------------------------
    Determines if a planet lies in a given house *relative to* another planet.

    ───────────────────────────────────────────────────────────────────────────
    ⚙️ RULES

    | **House #** | **Angular Range (°)** | **Inclusive / Exclusive Rule**   | **Astrological Interpretation**                           |
    | ----------- | --------------------- | -------------------------------- | --------------------------------------------------------- |
    | 1           | [0°, 30°)             | Inclusive lower, exclusive upper | Same sign / conjunction region.                           |
    | 2           | [30°, 60°)            | Inclusive lower, exclusive upper | One sign ahead – wealth, accumulation.                    |
    | 3           | [60°, 90°)            | Inclusive lower, exclusive upper | Courage, siblings, short journeys.                        |
    | 4           | [90°, 120°)           | Inclusive lower, exclusive upper | Home, comfort, mother, emotions.                          |
    | 5           | [120°, 150°)          | Inclusive lower, exclusive upper | Creativity, children, intelligence.                       |
    | 6           | [150°, 180°)          | Inclusive lower, exclusive upper | Service, competition, enemies.                            |
    | 7           | [180°, 210°)          | Inclusive lower, exclusive upper | Relationships, partnerships, marriage.                    |
    | 8           | [210°, 240°)          | Inclusive lower, exclusive upper | Transformation, longevity, occult.                        |
    | 9           | [240°, 270°)          | Inclusive lower, exclusive upper | Dharma, fortune, higher learning.                         |
    | 10          | [270°, 300°)          | Inclusive lower, exclusive upper | Career, karma, public life.                               |
    | 11          | [300°, 330°)          | Inclusive lower, exclusive upper | Gains, social circles, aspirations.                       |
    | 12          | [330°, 360°]          | Inclusive both ends              | Moksha, foreign lands, expenditure, liberation.           |

    Special handling:
    - Wrap-around at 360° is explicitly corrected.
    - If raw difference is exactly a multiple of 360°, map to 12th house.
    - Any computed house >12 is clamped to 12.
    ---------------------------------------------------------------------------
    """

    def _to_decimal_angle(self, value: float) -> Decimal:
        """Convert float longitude to quantized Decimal(°)."""
        return Decimal(str(value)).quantize(Decimal("0.0001"))

    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        try:
            planet_lon = provider.longitude(cond.planet.lower(), when)
            ref_lon = provider.longitude(cond.target.lower(), when)
            target_house = int(cond.value)

            ref_dec = self._to_decimal_angle(ref_lon)
            planet_dec = self._to_decimal_angle(planet_lon)

            raw_diff = planet_dec - ref_dec

            # Normalize to [0, 360)
            rel_angle = raw_diff % Decimal("360.0000")

            # Handle wrap-around negatives
            if rel_angle < 0:
                rel_angle += Decimal("360.0000")

            # Handle exact multiples of 360
            if raw_diff != 0 and (raw_diff % Decimal("360.0000")) == 0:
                rel_angle = Decimal("360.0000")

            # Compute relative house index
            rel_house = int((rel_angle // Decimal("30.0000")) + 1)

            # Clamp to [1, 12]
            if rel_house > 12:
                rel_house = 12

            logger.debug(
                f"[HouseRelativeHandler] planet={cond.planet}({planet_lon:.4f}°) "
                f"from={cond.target}({ref_lon:.4f}°) rel_angle={rel_angle:.4f}° -> rel_house={rel_house}"
            )

            if rel_house == target_house:
                logger.debug(f"[HouseRelativeHandler] SUCCESS: {cond.planet} in house {rel_house} from {cond.target}")
                return True

            logger.debug(f"[HouseRelativeHandler] FAIL: expected={target_house}, got={rel_house}")
            return False

        except Exception as e:
            logger.error(f"[HouseRelativeHandler] Failed for {cond.planet}-{cond.target}: {e}", exc_info=True)
            return False
