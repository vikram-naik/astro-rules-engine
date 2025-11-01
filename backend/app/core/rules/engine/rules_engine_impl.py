# app/core/rules/rules_engine_impl.py
from datetime import datetime
from typing import List, Dict, Any
from app.core.rules.interfaces.i_rules_engine import IRulesEngine
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from app.core.db.models import Rule, Condition  # ✅ use ORM directly
from app.core.db.enums import Relation
from app.core.common.config import settings
import logging

logger = logging.getLogger("astro.rulesengine")


def get_orb(planet_a: str, planet_b: str) -> float:
    """Determine orb based on planetary pair."""
    if not planet_a or not planet_b:
        return settings.orb_default
    key1 = f"{planet_a.lower()}-{planet_b.lower()}"
    key2 = f"{planet_b.lower()}-{planet_a.lower()}"
    return (
        settings.orb_overrides.get(key1)
        or settings.orb_overrides.get(key2)
        or settings.orb_default
    )


class RulesEngineImpl(IRulesEngine):
    """Evaluates nested condition groups and outcomes using ORM models."""

    def __init__(self, provider: IAstroProvider, orb_default: float = None):
        self.provider = provider
        self.orb_default = orb_default if orb_default is not None else settings.orb_default
        logger.debug(
            "RulesEngineImpl initialized with provider=%s orb_default=%s",
            getattr(self.provider, "__class__", type(self.provider)),
            self.orb_default,
        )

    # ------------------------------------------------------------
    # PUBLIC: Evaluate entire rule
    # ------------------------------------------------------------
    def evaluate_rule(self, rule: Rule, when: datetime) -> List[Dict[str, Any]]:
        """
        Evaluate a rule composed of nested condition groups.
        Returns a list of generated outcome events if satisfied.
        """
        logger.debug(
            "Evaluating rule id=%s name=%s groups=%d outcomes=%d",
            getattr(rule, "id", None),
            getattr(rule, "name", None),
            len(rule.condition_groups or []),
            len(rule.outcomes or []),
        )

        if not rule.condition_groups:
            logger.warning("Rule %s has no condition groups", getattr(rule, "name", None))
            return []

        satisfied = all(self._evaluate_group(g, when) for g in rule.condition_groups)

        if not satisfied:
            logger.debug("Rule %s NOT satisfied", getattr(rule, "name", None))
            return []

        logger.debug("Rule %s satisfied — generating outcomes", getattr(rule, "name", None))
        events = [
            {
                "rule_id": getattr(rule, "id", None),
                "date": (when.date() if hasattr(when, "date") else when).isoformat(),
                "effect": out.effect,
                "weight": out.weight,
                "confidence": rule.confidence,
            }
            for out in rule.outcomes
        ]

        logger.debug("Generated %d event(s)", len(events))
        return events

    # ------------------------------------------------------------
    # PRIVATE: Evaluate a single group (recursive)
    # ------------------------------------------------------------
    def _evaluate_group(self, group, when: datetime) -> bool:
        """Recursively evaluate a condition group tree."""
        group_results = []

        for cond in getattr(group, "conditions", []):
            result = self._check_condition(cond, when)
            group_results.append(result)
            logger.debug(
                "Condition check [%s %s %s] => %s",
                cond.planet,
                cond.relation,
                cond.target,
                result,
            )

        for subgroup in getattr(group, "subgroups", []):
            sub_result = self._evaluate_group(subgroup, when)
            group_results.append(sub_result)
            logger.debug(
                "Subgroup operator=%s result=%s",
                subgroup.operator,
                sub_result,
            )

        if not group_results:
            logger.debug("Empty group encountered, returning False")
            return False

        group_result = all(group_results) if group.operator == "AND" else any(group_results)
        logger.debug(
            "Group operator=%s aggregated_result=%s (from %d entries)",
            group.operator,
            group_result,
            len(group_results),
        )
        return group_result

    # ------------------------------------------------------------
    # PRIVATE: Evaluate one condition
    # ------------------------------------------------------------
    def _check_condition(self, cond: Condition, when: datetime) -> bool:
        from app.core.rules.relations.registry import get_relation_handler

        planet = (cond.planet or "").lower()
        relation = cond.relation
        if isinstance(relation, Relation):
            relation = relation.name

        target = (cond.target or "").lower()
        orb = cond.orb if cond.orb is not None else get_orb(planet, target)

        try:
            handler = get_relation_handler(Relation[relation])
            if handler is None:
                logger.warning("No relation handler registered for %s", relation)
                return False
            return handler.check(self.provider, cond, when, orb)
        except Exception as exc:
            logger.exception("Condition check failed for %s: %s", relation, exc)
            return False
