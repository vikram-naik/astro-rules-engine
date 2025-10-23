"""
SwissEphemProvider

SwissEphem-based implementation of IAstroProvider.
- Mode-aware (tropical, lahiri, krishnamurti, raman)
- Uses SwissEphemPlanetMapper for canonical-to-provider mapping
- Applies correct flag handling for sidereal vs tropical modes
- Fully consistent with SkyfieldProvider behavior and tests
"""

import os
import logging
from datetime import datetime
from typing import Union

import swisseph as swe

from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from app.core.astro.interfaces.i_planet_mapper import IPlanetMapper
from app.core.db.enums import Planet

logger = logging.getLogger("astro.swisseph")

HAS_SW = True


# -----------------------------------------------------------
# Planet Mapper
# -----------------------------------------------------------
class SwissEphemPlanetMapper(IPlanetMapper):
    """
    Maps canonical Planet enum members to SwissEphem planet IDs.
    """
    def __init__(self):
        self.map = {
            Planet.sun: swe.SUN,
            Planet.moon: swe.MOON,
            Planet.mercury: swe.MERCURY,
            Planet.venus: swe.VENUS,
            Planet.mars: swe.MARS,
            Planet.jupiter: swe.JUPITER,
            Planet.saturn: swe.SATURN,
            Planet.uranus: swe.URANUS,
            Planet.neptune: swe.NEPTUNE,
            Planet.pluto: swe.PLUTO,
            Planet.rahu: swe.MEAN_NODE,  # Rahu = Mean Lunar Node
            Planet.ketu: swe.MEAN_NODE,  # Ketu = opposite point
        }

    def resolve(self, planet: Planet) -> int:
        if planet not in self.map:
            raise KeyError(f"No mapping found for planet: {planet}")
        return self.map[planet]


# -----------------------------------------------------------
# SwissEphemProvider
# -----------------------------------------------------------
class SwissEphemProvider(IAstroProvider):
    def __init__(self):
        self.mode = os.getenv("ASTRO_AYANAMSA_MODE", "lahiri").lower()
        self.mapper = SwissEphemPlanetMapper()

        # Configure sidereal/tropical mode
        if self.mode in ("tropical", "none"):
            swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)  # effectively no ayanamsa shift
            self.is_sidereal = False
        elif self.mode == "lahiri":
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            self.is_sidereal = True
        elif self.mode == "krishnamurti":
            swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
            self.is_sidereal = True
        elif self.mode == "raman":
            swe.set_sid_mode(swe.SIDM_RAMAN)
            self.is_sidereal = True
        else:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            self.is_sidereal = True

        logger.info("SwissEphem provider initialized (mode=%s)", self.mode)

    # -------------------------------------------------------
    def longitude(self, planet: Union[str, Planet], when: datetime) -> float:
        """
        Return ecliptic longitude (degrees) for the planet at given datetime.
        Handles sidereal/tropical mode per provider settings.
        """
        # Normalize planet input
        if isinstance(planet, Planet):
            planet_enum = planet
        else:
            key = str(planet).strip().lower()
            if key in Planet.__members__:
                planet_enum = Planet.__members__[key]
            else:
                # fallback to match by enum value string
                matched = None
                for m in Planet:
                    if m.value.lower() == key:
                        matched = m
                        break
                if matched is None:
                    raise ValueError(f"Unsupported planet name: {planet}")
                planet_enum = matched

        planet_id = self.mapper.resolve(planet_enum)

        # Compute Julian day (UT)
        jd = swe.julday(
            when.year,
            when.month,
            when.day,
            when.hour + when.minute / 60.0 + when.second / 3600.0
        )

        # Determine calculation flags
        flags = swe.FLG_SWIEPH
        if getattr(self, "is_sidereal", False):
            flags |= swe.FLG_SIDEREAL

        # Compute planetary longitude
        res, ret = swe.calc_ut(jd, planet_id, flags)
        if len(res) >= 3:
            lon, lat, dist = res[0], res[1], res[2]
        else:
            lon, lat, dist = res[0], 0.0, 0.0

        # Adjust for Ketu (180° opposite node)
        if planet_enum == Planet.ketu:
            lon = (lon + 180.0) % 360.0

        logger.debug("SwissEphem calc: planet=%s jd=%.6f flags=%s lon=%.6f", planet_enum, jd, flags, lon)
        return lon % 360.0

    # -------------------------------------------------------
    def nakshatra_index(self, longitude_deg: float) -> int:
        """0..26 index (27 equal divisions of 360°)"""
        return int((float(longitude_deg) % 360.0) // (360.0 / 27.0))

    def nakshatra_owner(self, nak_idx: int) -> str:
        owners = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter"]
        return owners[int(nak_idx) % len(owners)]

    def angular_distance(self, a: float, b: float) -> float:
        """Shortest angular distance between two degrees on 0..360 circle."""
        return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)
