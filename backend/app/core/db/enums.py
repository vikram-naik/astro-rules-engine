from enum import Enum

class Planet(str, Enum):
    sun = "Sun"
    moon = "Moon"
    mars = "Mars"
    mercury = "Mercury"
    jupiter = "Jupiter"
    venus = "Venus"
    saturn = "Saturn"
    rahu = "Rahu"
    ketu = "Ketu"

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
