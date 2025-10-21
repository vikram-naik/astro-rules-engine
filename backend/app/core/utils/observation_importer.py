# backend/app/core/utils/observation_importer.py
"""
Observation Importer
--------------------
Parses Observations.txt and inserts structured astro rules
into the database using SQLModel models.

Features:
- Avoids duplicate rule insertion (based on name)
- Prints a complete summary table of all imported rules
- Safe session handling (no detached instance issues)
"""

import os
import re
import json
import uuid
import logging
from typing import List, Optional
from sqlalchemy import text
from tabulate import tabulate

from app.core.common.db import get_session
from app.core.common.models import RuleModel
from app.core.common.schemas import Condition, Outcome, OutcomeEffect, Relation
from app.core.common.logger import setup_logger

logger = setup_logger("INFO")

# --------------------------------------------------------------------
# Static dictionaries for parsing
# --------------------------------------------------------------------
PLANETS = [
    "sun", "moon", "mars", "mercury", "jupiter", "venus",
    "saturn", "rahu", "ketu", "gurudev"
]

SECTORS = {
    "bank": "BANK",
    "banking": "BANK",
    "auto": "AUTO",
    "metal": "METAL",
    "commodity": "METAL",
    "fmcg": "FMCG",
    "pharma": "PHARMA",
    "it": "IT",
    "energy": "ENERGY",
    "oil": "OIL",
    "defence": "DEFENCE",
    "infra": "INFRA",
    "equity": "EQUITY",
    "market": "EQUITY",
}

EFFECTS = {
    "bullish": OutcomeEffect.Bullish,
    "positive": OutcomeEffect.Bullish,
    "bearish": OutcomeEffect.Bearish,
    "negative": OutcomeEffect.Bearish,
}


# --------------------------------------------------------------------
# Helper detection functions
# --------------------------------------------------------------------
def _extract_planets(text: str) -> List[str]:
    return [p for p in PLANETS if p in text]


def _detect_relation(text: str) -> Relation:
    if "conjunct" in text or "conjunction" in text:
        return Relation.conjunct_with
    if "aspect" in text:
        return Relation.aspect_with
    if "nakshatra" in text:
        return Relation.in_nakshatra_owned_by
    if "axis" in text:
        return Relation.in_axis
    if "house" in text:
        return Relation.in_house_relative_to
    return Relation.in_sign


def _detect_sector(text: str) -> str:
    for s, code in SECTORS.items():
        if s in text:
            return code
    return "EQUITY"


def _detect_effect(text: str) -> OutcomeEffect:
    for k, e in EFFECTS.items():
        if k in text:
            return e
    if "correct" in text or "down" in text or "negative" in text:
        return OutcomeEffect.Bearish
    return OutcomeEffect.Bullish


# --------------------------------------------------------------------
# Core parsing logic
# --------------------------------------------------------------------
def parse_observation(line: str) -> Optional[RuleModel]:
    """Convert one line of Observations.txt into a RuleModel instance."""
    text_line = line.strip().lower()
    if not text_line or text_line.startswith("#"):
        return None

    planets = _extract_planets(text_line)
    if not planets:
        return None

    relation = _detect_relation(text_line)
    sector = _detect_sector(text_line)
    effect = _detect_effect(text_line)

    planet = planets[0]
    target = planets[1] if len(planets) > 1 else None

    rule_id = f"OBS_{uuid.uuid4().hex[:8]}"
    name = f"{planet.title()} {relation.value.replace('_', ' ')} {target.title() if target else ''}".strip()

    condition = Condition(planet=planet, relation=relation, target=target)
    outcome = Outcome(sector_code=sector, effect=effect, weight=1.0)

    rule = RuleModel(
        rule_id=rule_id,
        name=name,
        description=f"Imported from observation: {line.strip()}",
        conditions=json.dumps([condition.model_dump()]),
        outcomes=json.dumps([outcome.model_dump()]),
        enabled=True,
        confidence=0.8,
    )
    return rule


# --------------------------------------------------------------------
# Main import logic
# --------------------------------------------------------------------
def import_observations_file(path: str):
    """Read Observations.txt, parse each line, and insert valid rules."""
    logger.info(f"📥 Importing observations from {path}")
    if not os.path.exists(path):
        logger.error(f"❌ File not found: {path}")
        return

    with open(path, "r") as f:
        lines = f.readlines()

    # Parse rules
    parsed_rules: List[RuleModel] = []
    for line in lines:
        rule = parse_observation(line)
        if rule:
            parsed_rules.append(rule)

    if not parsed_rules:
        logger.warning("No valid observations found.")
        return

    inserted, skipped = 0, 0
    summary_data: List[List[str]] = []

    with get_session() as session:
        for rule in parsed_rules:
            stmt = text("SELECT rule_id FROM rulemodel WHERE name = :name").bindparams(name=rule.name)
            existing = session.exec(stmt).first()
            if existing:
                skipped += 1
                continue

            session.add(rule)
            inserted += 1

            # Cache summary data while session is active
            conds = json.loads(rule.conditions)
            outs = json.loads(rule.outcomes)
            summary_data.append([
                conds[0].get("planet", ""),
                conds[0].get("relation", ""),
                conds[0].get("target", ""),
                outs[0].get("sector_code", ""),
                outs[0].get("effect", ""),
                f"{rule.confidence:.2f}",
            ])

        session.commit()

    # Log summary
    logger.info(f"✅ Imported {inserted} new rules, skipped {skipped} duplicates.")
    if inserted > 0:
        print("\n📊  Imported Rules Summary:")
        print(tabulate(
            summary_data,
            headers=["Planet", "Relation", "Target", "Sector", "Effect", "Confidence"],
            tablefmt="fancy_grid"
        ))
    else:
        logger.info("No new rules added (all duplicates).")


# --------------------------------------------------------------------
# CLI entry point
# --------------------------------------------------------------------
def main():
    """Main entry point for CLI usage."""
    base = os.getcwd()
    path = os.path.join(base, "backend", "Observations.txt")
    if not os.path.exists(path):
        path = os.path.join(base, "Observations.txt")

    logger.info("🚀 Starting Observation Importer...")
    import_observations_file(path)
    logger.info("🏁 Import completed.")


if __name__ == "__main__":
    main()
