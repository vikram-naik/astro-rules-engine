"""
SwissEphemProvider
------------------
Implementation of IAstroProvider using pyswisseph for high-precision sidereal positions.
Requires: pip install pyswisseph
"""
from datetime import datetime
import math
import logging
from core.astro.interfaces.i_astro_provider import IAstroProvider

logger = logging.getLogger("astro.swisseph")

try:
    import swisseph as swe
    HAS_SW = True
except Exception as e:
    HAS_SW = False
    logger.warning(f"pyswisseph not available: {e}")

class SwissEphemProvider(IAstroProvider):
    """Swiss Ephemeris-based implementation of IAstroProvider."""

    def __init__(self, ayanamsa: int = 1):  # 1 = Lahiri
        self.ayanamsa = ayanamsa
        if HAS_SW:
            swe.set_sid_mode(self.ayanamsa)

    def longitude(self, planet: str, when: datetime) -> float:
        if not HAS_SW:
            raise RuntimeError("pyswisseph not installed.")
        jd = swe.julday(when.year, when.month, when.day,
                        when.hour + when.minute / 60.0 + when.second / 3600.0)
        body_map = {
            "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
            "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
            "saturn": swe.SATURN, "uranus": swe.URANUS, "neptune": swe.NEPTUNE,
            "pluto": swe.PLUTO
        }
        if planet in ["rahu", "ketu"]:
            lon = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
            if planet == "ketu":
                lon = (lon + 180) % 360
            return lon % 360
        if planet not in body_map:
            raise ValueError(f"Unsupported planet: {planet}")
        lon = swe.calc_ut(jd, body_map[planet])[0][0]
        return lon % 360

    def nakshatra_index(self, longitude_deg: float) -> int:
        return int(math.floor((longitude_deg % 360.0) / (360.0 / 27.0)))

    def nakshatra_owner(self, nak_idx: int) -> str:
        owners = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter"]
        return owners[nak_idx % len(owners)]

    def angular_distance(self, a: float, b: float) -> float:
        return abs((a - b + 180) % 360 - 180)
