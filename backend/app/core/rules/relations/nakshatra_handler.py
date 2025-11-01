# app/core/rules/relations/nakshatra_handler.py
from datetime import datetime
from app.core.db.models import Condition
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

class NakshatraOwnedHandler(IRelationHandler):
    """
    NakshatraOwnedHandler
    ---------------------
    Astrological Meaning:
        In Vedic astrology, the zodiac is divided into 27 Nakshatras (lunar mansions).
        Each Nakshatra has a *planetary ruler* (owner), and a planet placed within
        a given Nakshatra is said to be “in the domain of” its ruler — symbolizing
        influence and control by that ruler.

    Functional Logic:
        This handler checks whether a planet lies in a Nakshatra owned by
        a target planet.

    Evaluation Steps:
        1. Get the planet’s ecliptic longitude from the provider.
        2. Determine which Nakshatra index this longitude corresponds to
        using `provider.nakshatra_index(lon)`.
        3. Retrieve the owner planet of that Nakshatra via
        `provider.nakshatra_owner(nk)`.
        4. Compare the normalized owner name to the target planet in
        the rule condition.

    Return Value:
        - **True** if the planet’s Nakshatra owner matches the target planet name.
        - **False** otherwise.
        - **False** if any provider method raises (e.g., missing data, invalid planet).

    Example:
        # Check if Moon is in a Nakshatra owned by Venus
        cond = ConditionRead(planet="moon", relation=Relation.in_nakshatra_owned_by, target="venus")
        handler.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)
    """

    def check(self, provider: IAstroProvider, cond: Condition, when: datetime, orb_default: float) -> bool:
        planet = (cond.planet or "").lower()
        owner_target = (cond.target or "").lower()
        try:
            lon = provider.longitude(planet, when)
            nk = provider.nakshatra_index(lon)
            owner = provider.nakshatra_owner(nk)
        except Exception:
            return False
        return owner.lower() == owner_target
