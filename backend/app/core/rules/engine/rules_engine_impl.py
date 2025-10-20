from datetime import datetime
from typing import List, Dict, Any
from core.rules.interfaces.i_rules_engine import IRulesEngine
from core.astro.interfaces.i_astro_provider import IAstroProvider
from core.common.schemas import RuleCreate, Condition, Relation

class RulesEngineImpl(IRulesEngine):
    """Concrete rules engine depending on IAstroProvider abstraction."""

    def __init__(self, provider: IAstroProvider, orb_default: float = 5.0):
        self.provider = provider
        self.orb_default = orb_default

    def evaluate_rule(self, rule: RuleCreate, when: datetime) -> List[Dict[str, Any]]:
        for cond in rule.conditions:
            if not self._check_condition(cond, when):
                return []
        events = []
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

    def _check_condition(self, cond: Condition, when: datetime) -> bool:
        planet = (cond.planet or "").lower()
        relation = cond.relation
        target = (cond.target or "").lower()
        orb = cond.orb if cond.orb is not None else self.orb_default

        try:
            lon = self.provider.longitude(planet, when)
        except Exception:
            return False

        if relation == Relation.in_nakshatra_owned_by:
            nk = self.provider.nakshatra_index(lon)
            owner = self.provider.nakshatra_owner(nk)
            return owner.lower() == target.lower()

        if relation == Relation.conjunct_with:
            tlon = self.provider.longitude(target, when)
            return self.provider.angular_distance(lon, tlon) <= orb

        if relation == Relation.in_axis:
            tlon = self.provider.longitude(target, when)
            if self.provider.angular_distance(lon, tlon) <= orb:
                return True
            if self.provider.angular_distance(lon, (tlon + 180) % 360) <= orb:
                return True
            return False

        if relation == Relation.in_sign:
            sign = int((lon // 30) % 12)
            return sign == int(cond.value)

        if relation == Relation.in_house_relative_to:
            ref_lon = self.provider.longitude(target, when)
            house = int(cond.value)
            center = (ref_lon + (house - 1) * 30) % 360
            return self.provider.angular_distance(lon, center) <= orb

        if relation == Relation.aspect_with:
            tlon = self.provider.longitude(target, when)
            asp = float(cond.value) if cond.value is not None else 0.0
            return abs(self.provider.angular_distance(lon, tlon) - asp) <= orb

        return False
