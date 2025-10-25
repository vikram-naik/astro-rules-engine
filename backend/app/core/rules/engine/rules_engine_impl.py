from datetime import datetime
from typing import List, Dict, Any
from app.core.rules.interfaces.i_rules_engine import IRulesEngine
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from app.core.common.schemas import RuleCreate, ConditionRead
from app.core.db.enums import Relation
import logging
logger = logging.getLogger("astro.rulesengine")

class RulesEngineImpl(IRulesEngine):
    """Concrete rules engine depending on IAstroProvider abstraction."""

    def __init__(self, provider: IAstroProvider, orb_default: float = 5.0):
        self.provider = provider
        self.orb_default = orb_default
        logger.debug("RulesEngineImpl initialized with provider=%s orb_default=%s",
             getattr(self.provider, "__class__", type(self.provider)), orb_default)


    def evaluate_rule(self, rule: RuleCreate, when: datetime) -> List[Dict[str, Any]]:
        logger.debug("evaluate_rule: rule_id=%s when=%s conditions=%d outcomes=%d",
             getattr(rule, "rule_id", None), when.isoformat(), len(rule.conditions or []), len(rule.outcomes or []))

        for cond in rule.conditions:
            if not self._check_condition(cond, when):
                return []
        events = []
        for out in rule.outcomes:
            logger.debug(f"oc: {out}")
            events.append({
                "rule_id": rule.rule_id,
                "date": (when.date() if hasattr(when, "date") else when).isoformat(),
                "sector": out.sector.code,
                "effect": out.effect,
                "weight": out.weight,
                "confidence": rule.confidence
            })
        logger.debug("evaluate_rule -> events_count=%d events=%s", len(events), events)
        return events

    def _check_condition(self, cond: ConditionRead, when: datetime) -> bool:
        from app.core.rules.relations.registry import get_relation_handler
        planet = (cond.planet or "").lower()
        relation = Relation[cond.relation]
        target = (cond.target or "").lower()
        orb = cond.orb if cond.orb is not None else self.orb_default
        logger.debug("Checking condition: planet=%s relation=%s target=%s orb=%s", planet, relation, target, orb)

        try:
            lon = self.provider.longitude(planet, when)
            logger.debug("Provider longitude: planet=%s when=%s lon=%.6f", planet, when.isoformat(), lon)
        except Exception as exc:
            logger.exception("Provider.longitude failed for planet=%s when=%s: %s", planet, when, exc)
            return False

        # Delegate to dedicated handler (registered in app/core/rules/relations)
        handler = get_relation_handler(relation)
        if handler is None:
            logger.warning("No relation handler registered for relation=%s (condition=%s)", relation, cond)
            return False

        try:
            result = handler.check(self.provider, cond, when, self.orb_default)
            logger.debug("Relation handler result: relation=%s result=%s", relation, result)
            return result
        except Exception as exc:
            logger.exception("Relation handler raised exception for relation=%s cond=%s: %s", relation, cond, exc)
            return False
