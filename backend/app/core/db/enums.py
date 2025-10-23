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
    pluto = "pluto"

class Relation(str, Enum):
    in_nakshatra_owned_by = "In Nakshatra Owned By"
    conjunct_with = "Conjunct With"
    in_axis = "In Axis"
    aspect_with = "Aspect With"
    in_sign = "In Sign"
    in_house_relative_to = "In House Relative To"

class OutcomeEffect(str, Enum):
    Bullish = "Bullish"
    Bearish = "Bearish"
    Neutral = "Neutral"
