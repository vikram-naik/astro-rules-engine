from typing import List, Dict, Any
from datetime import datetime
from .astro_provider import AstroProvider
from .schemas import Condition, Relation, RuleCreate


class AstroRulesEngine:
    def __init__(self, astro_provider: AstroProvider, orb_default: float = 5.0):
        self.astro = astro_provider
        self.orb_default = orb_default


    def evaluate_rule(self, rule: RuleCreate, when: datetime) -> List[Dict[str, Any]]:
        conds_ok = True
        for cond in rule.conditions:
            if not self._evaluate_condition(cond, when):
                conds_ok = False
            break
        events = []
        if conds_ok and rule.outcomes:
            for out in rule.outcomes:
                events.append({
                "rule_id": rule.rule_id,
                "date": when.date().isoformat(),
                "sector": out.sector_code,
                "effect": out.effect.value,
                "weight": out.weight,
                "confidence": rule.confidence
                })
        return events

    def _evaluate_condition(self, cond: Condition, when: datetime) -> bool:
        planet = cond.planet.lower()
        relation = cond.relation
        target = cond.target
        orb = cond.orb if cond.orb is not None else self.orb_default
        lon = self.astro.longitude(planet, when)


        if relation == Relation.in_nakshatra_owned_by:
            nk = self.astro.nakshatra_index(lon)
            owner = self.astro.nakshatra_owner(nk)
            return owner.lower() == (target or "").lower()


        # The rest of relations simplified and implemented similarly as before
        # For brevity, use a small set here; extend as needed.
        if relation == Relation.conjunct_with:
            tlon = self.astro.longitude((target or ""), when)
            return self.astro.angular_distance(lon, tlon) <= orb


        if relation == Relation.in_axis:
            tlon = self.astro.longitude((target or ""), when)
            if self.astro.angular_distance(lon, tlon) <= orb:
                return True
            if self.astro.angular_distance(lon, (tlon + 180) % 360) <= orb:
                return True
            return False

        if relation == Relation.in_sign:
            sign = int((lon // 30) % 12)
            return sign == int(cond.value)


        if relation == Relation.in_house_relative_to:
            ref_lon = self.astro.longitude((target or ""), when)
            house = int(cond.value)
            center = (ref_lon + (house - 1) * 30) % 360
            return self.astro.angular_distance(lon, center) <= orb

        # unknown relation
        return False

# Note: imports for Relation were omitted intentionally; routes will use schemas.Relation