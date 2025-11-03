# app/core/db/enums.py
from enum import Enum


class Planet(str, Enum):
    """Canonical planet enumeration for astro logic."""
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


class RelationData:
    """Encapsulates metadata for each relation."""
    def __init__(
        self,
        label,
        target_source="planets",
        has_orb=True,
        has_value=False,
        requires_target=True,
        requires_planet=True,
    ):
        self.label = label
        self.target_source = target_source  # "planets", "signs", "none"
        self.has_orb = has_orb
        self.has_value = has_value
        self.requires_target = requires_target
        self.requires_planet = requires_planet


class Relation(Enum):
    # Core relations
    in_nakshatra_owned_by = RelationData("In Nakshatra Owned By", target_source="planets", has_orb=False)
    conjunct_with = RelationData("Conjunct With", target_source="planets", has_orb=True)
    in_axis = RelationData("In Axis", target_source="planets", has_orb=False)
    aspect_with = RelationData("Aspect With", target_source="planets", has_orb=True, has_value=True)
    in_sign = RelationData("In Sign", target_source="signs", has_orb=False)
    in_house_relative_to = RelationData("In House Relative To", target_source="planets", has_orb=False)

    # Standard aspects
    opposition_with = RelationData("Opposition (180°)")
    trine_with = RelationData("Trine (120°)")
    square_with = RelationData("Square (90°)")
    sextile_with = RelationData("Sextile (60°)")
    quincunx_with = RelationData("Quincunx / Inconjunct (150°)")
    semisextile_with = RelationData("Semisextile (30°)")
    semisquare_with = RelationData("Semisquare (45°)")
    quintile_with = RelationData("Quintile (72°)")
    sesquiquadrate_with = RelationData("Sesquiquadrate (135°)")

    # Special conditions
    combust_by_sun = RelationData("Combust by Sun", requires_target=False, target_source="none", has_orb=True)
    is_retrograde = RelationData(
        "Is Retrograde",
        target_source="none",
        has_orb=False,
        requires_target=False,
        requires_planet=True,
    )
    melifics_in_kendra = RelationData(
        "Malefics in Kendra",
        target_source="none",
        has_orb=False,
        requires_target=False,
        requires_planet=False,
    )


class Sign(str, Enum):
    """Zodiac signs mapped to indices 0–11."""
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


class AyanamsaMode(str, Enum):
    lahiri = "lahiri"
    raman = "raman"
    krishnamurti = "krishnamurti"
    tropical = "tropical"


# ---------------------------------------------------------------------
# 🔤 i18n support helpers
# ---------------------------------------------------------------------

def enum_to_ref(enum_cls):
    """
    Convert an Enum class to a list of dicts usable by the frontend REF loader.
    Each item includes a stable i18n translation key.
    """
    items = []
    for e in enum_cls:
        # Each enum entry may hold a RelationData or a simple str
        label = getattr(e.value, "label", str(e.value))
        items.append({
            "key": e.name,
            "label": label,
            "i18n": f"{enum_cls.__name__.lower()}.{e.name}"
        })
    return items


# Example (used in routes_reference_api.py or wherever REF is built):
#
# from app.core.db.enums import enum_to_ref, Planet, Relation, Sign
#
# REF = {
#     "planets": enum_to_ref(Planet),
#     "relations": enum_to_ref(Relation),
#     "signs": enum_to_ref(Sign),
#     ...
# }
#
# Each dict now looks like:
#   {"key": "sun", "label": "Sun", "i18n": "planet.sun"}
