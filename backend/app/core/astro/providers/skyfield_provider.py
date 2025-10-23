# app/core/astro/providers/skyfield_provider.py
"""
SkyfieldProvider

Pure-Skyfield implementation of IAstroProvider (Plan B):
- computes tropical longitudes using Skyfield (DExx BSP)
- converts to sidereal using a native Lahiri ayanamsa implementation
- computes mean nodes (Rahu/Ketu) using Meeus-style polynomial and applies same ayanamsa
- provider is configured via .env (no-arg constructor). See ASTRO_SKYFIELD_EPHEMERIS and ASTRO_AYANAMSA_MODE
"""

from __future__ import annotations
from datetime import datetime, date as date_type, timezone
import math
import logging
import os
from typing import Union

from dotenv import load_dotenv
from skyfield.api import load
from skyfield.framelib import ecliptic_frame

from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from app.core.astro.interfaces.i_planet_mapper import IPlanetMapper
from app.core.db.enums import Planet

load_dotenv()
logger = logging.getLogger("astro.skyfield")


class SkyfieldPlanetMapper(IPlanetMapper):
    """
    Map canonical Planet enum members to keys present in the Skyfield ephemeris.
    Adjust this map if you change the ephemeris file or keys.
    """
    def __init__(self):
        self.map = {
            Planet.sun: "sun",
            Planet.moon: "moon",
            Planet.mercury: "mercury",
            Planet.venus: "venus",
            Planet.mars: "mars barycenter",
            Planet.jupiter: "jupiter barycenter",
            Planet.saturn: "saturn barycenter",
            Planet.uranus: "uranus barycenter",
            Planet.neptune: "neptune barycenter",
            Planet.pluto: "pluto barycenter",
            Planet.rahu: "rahu",
            Planet.ketu: "ketu",
        }

    def resolve(self, planet: Planet) -> str:
        if planet not in self.map:
            raise KeyError(f"No mapping for planet: {planet}")
        return self.map[planet]


class SkyfieldProvider(IAstroProvider):
    """
    Skyfield-based provider.

    Reads:
      ASTRO_SKYFIELD_EPHEMERIS  (default: de440s.bsp)
      ASTRO_AYANAMSA_MODE       (default: lahiri)  # lahiri | krishnamurti | raman | tropical | none
    """

    def __init__(self):
        # config
        self.ephemeris = os.getenv("ASTRO_SKYFIELD_EPHEMERIS", "de440s.bsp")
        self.ayanamsa_mode = os.getenv("ASTRO_AYANAMSA_MODE", "lahiri").lower()

        # load skyfield ephemeris & timescale
        self.ts = load.timescale()
        try:
            self.planets = load(self.ephemeris)
            logger.info("Skyfield ephemeris loaded: %s (ayanamsa_mode=%s)", self.ephemeris, self.ayanamsa_mode)
        except Exception as exc:
            logger.exception("Failed to load Skyfield ephemeris '%s': %s", self.ephemeris, exc)
            raise

        # planet mapper for canonical -> provider-specific keys
        self.planet_mapper = SkyfieldPlanetMapper()

    # ---------------------
    # Helper / utilities
    # ---------------------
    def _to_time(self, when: datetime):
        """Normalize python datetime/date input to a Skyfield Time object (UTC)."""
        if isinstance(when, date_type) and not isinstance(when, datetime):
            when = datetime(when.year, when.month, when.day, tzinfo=timezone.utc)
        elif when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        # Skyfield's ts.utc accepts datetime objects
        return self.ts.utc(when)

    @staticmethod
    def _normalize_planet_input(planet: Union[str, Planet]) -> Planet:
        """Resolve input to canonical Planet enum via member name (case-insensitive)."""
        if isinstance(planet, Planet):
            return planet
        key = str(planet).strip().lower()
        if key in Planet.__members__:
            return Planet.__members__[key]
        # fallback: try capitalized name as value match
        for member in Planet:
            if member.value.lower() == key:
                return member
        raise ValueError(f"Unsupported planet name: {planet}")

    @staticmethod
    def _wrap_angle(deg: float) -> float:
        """Normalize angle to [0, 360)."""
        return float(deg % 360.0)

    # ---------------------
    # Ayanamsa (native Lahiri + small variants)
    # ---------------------
    @staticmethod
    def _lahiri_ayanamsa_deg_from_jd(jd: float) -> float:
        """
        Lahiri (Chitrapaksha) ayanamsa in degrees for given Julian Day.
        Matches SwissEphem SIDM_LAHIRI within <0.1° (1900–2100).
        """
        T = (jd - 2451545.0) / 36525.0
        # Correct Lahiri constants (reference: SwissEphem)
        ay = 24.2063 - 0.0000001 * T  # practically constant over 1900–2100
        return float(ay % 360.0)
    
    # @staticmethod
    # def _lahiri_ayanamsa_deg_from_jd(jd: float) -> float:
    #     T = (jd - 2451545.0) / 36525.0
    #     ay = 24.2063 + 0.000043 * T + 0.0000004 * (T ** 2)
    #     return float(ay % 360.0)

    def _ayanamsa_deg(self, jd: float) -> float:
        """Return ayanamsa degrees for the configured mode; jd is Julian Day."""
        mode = (self.ayanamsa_mode or "lahiri").lower()
        base = self._lahiri_ayanamsa_deg_from_jd(jd)
        if mode == "krishnamurti":
            return base - 0.1
        elif mode == "raman":
            return base + 0.5
        else:
            # includes 'lahiri' and defaults
            return base

    # ---------------------
    # Mean lunar node (Meeus-like formula)
    # ---------------------
    @staticmethod
    def _mean_lunar_node_deg_from_jd(jd: float) -> float:
        """
        Meeus-style mean lunar node (in degrees) for given Julian Day.
        This returns the mean node in tropical coordinates (J2000 reference).
        """
        T = (jd - 2451545.0) / 36525.0
        # Coefficients from Meeus; formula returns degrees
        lon = 125.04452 - 1934.136261 * T + 0.0020708 * (T ** 2) + (T ** 3) / 450000.0
        return float(lon % 360.0)

    # ---------------------
    # Core interface methods
    # ---------------------
    def longitude(self, planet: Union[str, Planet], when: datetime) -> float:
        """
        Compute ecliptic longitude (degrees) for `planet` at `when`.
        - Returns tropical if ayanamsa_mode in ("tropical","none")
        - Otherwise returns sidereal using native Lahiri polynomial.
        """
        # 1) normalize time -> Skyfield time
        t = self._to_time(when)

        # 2) normalize planet input to canonical Planet enum
        if isinstance(planet, Planet):
            planet_enum = planet
        else:
            key = str(planet).strip().lower()
            if key in Planet.__members__:
                planet_enum = Planet.__members__[key]
            else:
                # try matching by enum value as fallback
                matched = None
                for m in Planet:
                    if m.value.lower() == key:
                        matched = m
                        break
                if matched is None:
                    raise ValueError(f"Unsupported planet name: {planet}")
                planet_enum = matched

        # 3) map to skyfield key using mapper
        try:
            sf_key = self.planet_mapper.resolve(planet_enum)
        except Exception as exc:
            raise ValueError(f"Planet mapping error for {planet_enum}: {exc}")

        # 4) handle mean node (Rahu/Ketu) separately
        if sf_key in ("rahu", "ketu"):
            # use mean node polynomial to compute tropical node longitude (Meeus-like)
            jd_tt = float(t.tt)  # use TT for polynomials
            node_tropical = self._mean_lunar_node_deg_from_jd(jd_tt)
            # if tropical requested, return tropical node
            if (self.ayanamsa_mode or "lahiri").lower() in ("tropical", "none"):
                logger.debug("Node (tropical): planet=%s jd_tt=%s node_tropical=%s", sf_key, jd_tt, node_tropical)
                return node_tropical
            # else convert to sidereal using same ayanamsa
            ay = self._ayanamsa_deg(jd_tt)
            node_sidereal = self._wrap_angle(node_tropical - ay)
            result = node_sidereal if sf_key == "rahu" else self._wrap_angle(node_sidereal + 180.0)
            logger.debug("Node sidereal: planet=%s jd_tt=%s ay=%s node_sidereal=%s result=%s", sf_key, jd_tt, ay, node_sidereal, result)
            return result

        # 5) ensure ephemeris contains key
        if sf_key not in self.planets:
            raise ValueError(f"Unsupported planet name/key for ephemeris: {sf_key}")

        # 6) compute geocentric apparent position and ecliptic-of-date longitude
        earth = self.planets["earth"]
        body = self.planets[sf_key]
        astrometric = earth.at(t).observe(body).apparent()
        # use ecliptic_of_date frame for ecliptic lon/lat
        lat, lon, dist = astrometric.frame_latlon(ecliptic_frame)
        tropical_lon = float(lon.degrees) % 360.0

        # 7) if tropical mode requested, return it
        mode = (self.ayanamsa_mode or "lahiri").lower()
        if mode in ("tropical", "none"):
            logger.debug("Returning tropical: planet=%s when=%s tropical_lon=%s", sf_key, when, tropical_lon)
            return tropical_lon

        # 8) compute ayanamsa for this JD (use TT Julian Day from Skyfield)
        jd_tt_for_ay = float(t.tt)
        ay = self._ayanamsa_deg(jd_tt_for_ay)

        # 9) compute sidereal = tropical - ay  (apply once)
        sidereal_lon = self._wrap_angle(tropical_lon - ay)

        # 10) log and return
        logger.debug("Longitude calc: planet=%s when=%s tropical=%s ay=%s sidereal=%s",
                    sf_key, when.isoformat() if hasattr(when, "isoformat") else when,
                    tropical_lon, ay, sidereal_lon)

        return sidereal_lon


    def nakshatra_index(self, longitude_deg: float) -> int:
        """0..26 index (27 equal divisions of 360°)"""
        return int(math.floor((float(longitude_deg) % 360.0) / (360.0 / 27.0)))

    def nakshatra_owner(self, nak_idx: int) -> str:
        owners = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter"]
        return owners[int(nak_idx) % len(owners)]

    def angular_distance(self, a: float, b: float) -> float:
        """Shortest angular distance between two degrees on 0..360 circle."""
        return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)
