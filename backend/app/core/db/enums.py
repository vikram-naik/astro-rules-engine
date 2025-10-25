# app/core/db/enums.py
from enum import Enum

class Planet(str, Enum):
    """
    Canonical planet enumeration for astro logic.
    Access by lowercase key, e.g. Planet['sun'], Planet['mars'].
    Enum values are human-readable display names.
    """
    sun = "Sun"
    moon = "Moon"
    mars = "Mars"
    mercury = "Mercury"
    jupiter = "Jupiter"
    venus = "Venus"
    saturn = "Saturn"
    rahu = "Rahu"
    ketu = "Ketu"
    uranus = "Uranus"
    neptune = "Neptune"
    pluto = "Pluto"


class Relation(str, Enum):
    # Existing high level relations
    in_nakshatra_owned_by = "In Nakshatra Owned By"
    conjunct_with = "Conjunct With"
    in_axis = "In Axis"
    aspect_with = "Aspect With"          # generic numeric aspect (value = degrees)
    in_sign = "In Sign"
    in_house_relative_to = "In House Relative To"

    # Explicit named aspects (Vedic/Astro oriented; technical key -> user friendly label)
    opposition_with = "Opposition (180°)"
    trine_with = "Trine (120°)"
    square_with = "Square (90°)"
    sextile_with = "Sextile (60°)"
    quincunx_with = "Quincunx / Inconjunct (150°)"
    semisextile_with = "Semisextile (30°)"
    semisquare_with = "Semisquare (45°)"
    quintile_with = "Quintile (72°)"
    sesquiquadrate_with = "Sesquiquadrate (135°)"

    # Additional astrological relations
    combust_by_sun = "Combust by Sun"
    retrograde = "Retrograde"
    # Future: combustion_by_planet, stationary, etc.

class Sign(str, Enum):
    """Zodiac signs, mapped to indices 0..11 (Aries = 0). Values are friendly names."""
    aries = "Aries"
    taurus = "Taurus"
    gemini = "Gemini"
    cancer = "Cancer"
    leo = "Leo"
    virgo = "Virgo"
    libra = "Libra"
    scorpio = "Scorpio"
    sagittarius = "Sagittarius"
    capricorn = "Capricorn"
    aquarius = "Aquarius"
    pisces = "Pisces"

class OutcomeEffect(str, Enum):
    Bullish = "Bullish"
    Bearish = "Bearish"
    Neutral = "Neutral"
