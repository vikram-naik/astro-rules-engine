"""
SwissEphemProvider

SwissEphem-based implementation of IAstroProvider.
- Mode-aware (tropical, lahiri, krishnamurti, raman)
- Uses SwissEphemPlanetMapper for canonical-to-provider mapping
- Applies correct flag handling for sidereal vs tropical modes
- Fully consistent with SkyfieldProvider behavior and tests
"""

import logging
from typing import Union
from datetime import datetime, timezone

from zoneinfo import ZoneInfo
import swisseph as swe

from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from app.core.astro.interfaces.i_planet_mapper import IPlanetMapper
from app.core.db.enums import AyanamsaMode, Planet
from app.core.astro.providers._mixin import AstroTimeMixin

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
class SwissEphemProvider(IAstroProvider, AstroTimeMixin):
    def __init__(self, ayanamsa_mode: AyanamsaMode = AyanamsaMode.lahiri):
        self.ayanamsa_mode = ayanamsa_mode
        self.planet_mappper = SwissEphemPlanetMapper()

        # Configure sidereal/tropical mode
        if self.ayanamsa_mode == AyanamsaMode.tropical:
            swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)  # no sidereal correction
            self.is_sidereal = False
        elif self.ayanamsa_mode == AyanamsaMode.lahiri:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            self.is_sidereal = True
        elif self.ayanamsa_mode == AyanamsaMode.krishnamurti:
            swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
            self.is_sidereal = True
        elif self.ayanamsa_mode == AyanamsaMode.raman:
            swe.set_sid_mode(swe.SIDM_RAMAN)
            self.is_sidereal = True
        else:
             raise NotImplementedError(f"Unsupported ayanamsa mode: {self.ayanamsa_mode}")
        logger.info("SwissEphem provider initialized (mode=%s)", self.ayanamsa_mode)


    def configure(self, location: dict | None = None, tz_name: str | None = None):
        """
        Configure topocentric coordinates and timezone.
        - location: {"lat": float, "lon": float, "alt": float}
        - tz_name: e.g. "Asia/Kolkata"
        """
        location = location or {}
        self.lat = float(location.get("lat", 0.0))
        self.lon = float(location.get("lon", 0.0))
        self.alt = float(location.get("alt", 0.0))

        try:
            self.tz = ZoneInfo(tz_name or "UTC")
        except Exception:
            self.tz = timezone.utc

        try:
            swe.set_topo(self.lon, self.lat, self.alt)
            logger.info(f"SwissEphem configured: lat={self.lat}, lon={self.lon}, alt={self.alt}, tz={self.tz}")
        except Exception as e:
            logger.warning(f"SwissEphem configure: failed to set topo — {e}")
            swe.set_topo(0.0, 0.0, 0.0)

        return self



    # -------------------------------------------------------

    def _normalize_when(self, when):
        return self._normalize_when_utc(when)
    
    # -------------------------------------------------------
    def longitude(self, planet: Union[str, Planet], when: datetime) -> float:
        """
        Compute ecliptic longitude (degrees) for the planet at the given datetime.
        - Converts local time → UTC using self.tz
        - Uses topocentric position (set via swe.set_topo)
        - Returns tropical/sidereal based on ayanamsa_mode
        """
        # --- 1. Normalize datetime ---
        when_utc = self._normalize_when(when)
        jd_ut = swe.julday(
            when_utc.year,
            when_utc.month,
            when_utc.day,
            when_utc.hour + when_utc.minute / 60.0 + when_utc.second / 3600.0,
        )

        # --- 2. Resolve planet ---
        if isinstance(planet, Planet):
            planet_enum = planet
        else:
            key = str(planet).strip().lower()
            if key in Planet.__members__:
                planet_enum = Planet.__members__[key]
            else:
                raise NotImplementedError(f"Unsupported planet name: {planet}")
        planet_id = self.planet_mappper.resolve(planet_enum)

        # --- 3. Flags & Calculation ---
        flags = swe.FLG_SWIEPH
        if getattr(self, "is_sidereal", False):
            flags |= swe.FLG_SIDEREAL

        res, ret = swe.calc_ut(jd_ut, planet_id, flags)
        lon = float(res[0])

        # --- 4. Adjust for Ketu ---
        if planet_enum == Planet.ketu:
            lon = (lon + 180.0) % 360.0

        # --- 5. Return ---
        logger.debug(
            f"[SwissEphem] planet={planet_enum.name}, when(local)={when}, UTC={when_utc}, "
            f"lon={lon:.4f}, mode={self.ayanamsa_mode.value}, loc=({getattr(self, 'lat', 0)}, {getattr(self, 'lon', 0)})"
        )
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

    def is_retrograde(self, planet: str, when: datetime) -> bool:
        """
        Return True if the specified planet is retrograde at the given time.
        Uses the provider's planet_mapper to look up the swisseph body code and reads
        the longitudinal speed from swe.calc_ut result (res[3]).
        """
        try:
            key = (planet or "").lower()
            logger.debug(f"is_retrograde: planet={key} when={when}")
            body_code = self.planet_mappper.resolve(Planet[key.lower()])
            if body_code is None:
                return False

            # Normalize to UTC datetime
            when_utc = self._normalize_when(when)
            jd = swe.julday(
                when_utc.year,
                when_utc.month,
                when_utc.day,
                when_utc.hour + when_utc.minute / 60.0 + when_utc.second / 3600.0
            )

            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            if getattr(self, "is_sidereal", False):
                flags |= swe.FLG_SIDEREAL

            res, ret = swe.calc_ut(jd, body_code, flags)
            if not res or len(res) < 4:
                return False

            speed_lon = float(res[3])
            logger.debug(f"is_retrograde: speed_lon={speed_lon}")
            # consider near-zero as retrograde (stationary) to match JPL behavior
            return speed_lon < -1e-5 or abs(speed_lon) < 0.02

        except Exception as e:
            logger.exception(f"Unexpected Exception : {e}", exc_info=True)
            return False
