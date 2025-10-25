# backend/app/core/common/schemas.py

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from app.core.db.enums import Relation, OutcomeEffect
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, ConfigDict



# --------------------------------------------------------------------
# CONDITION schemas
# --------------------------------------------------------------------
class ConditionBase(SQLModel):
    planet: str
    relation: Relation
    target: Optional[str] = None
    orb: Optional[float] = 5.0
    value: Optional[float] = None
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ConditionCreate(ConditionBase):
    """Used for creation via API or rule update."""
    pass


class ConditionRead(ConditionBase):
    """Used for reading from DB or returning via API."""
    id: int
    rule_id: int


# --------------------------------------------------------------------
# OUTCOME schemas
# --------------------------------------------------------------------
class OutcomeBase(SQLModel):
    sector_code: str
    effect: OutcomeEffect
    weight: float = 1.0
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class OutcomeCreate(OutcomeBase):
    pass


class OutcomeRead(OutcomeBase):
    id: int
    rule_id: int


# --------------------------------------------------------------------
# RULE schemas
# --------------------------------------------------------------------
class RuleBase(SQLModel):
    name: str
    description: Optional[str] = None
    confidence: float = 1.0
    enabled: bool = True
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class RuleCreate(RuleBase):
    rule_id: Optional[str] = None
    conditions: List[ConditionCreate] = []
    outcomes: List[OutcomeCreate] = []


class RuleRead(RuleBase):
    id: int
    rule_id: str
    created_at: datetime
    updated_at: datetime
    conditions: List[ConditionRead] = []
    outcomes: List[OutcomeRead] = []


class RuleUpdate(RuleBase):
    """Allows partial updates of fields and replacement of conditions/outcomes."""
    conditions: List[ConditionCreate] = []
    outcomes: List[OutcomeCreate] = []


# --------------------------------------------------------------------
# Example JSON schema extras for OpenAPI (unchanged pattern)
# --------------------------------------------------------------------
RuleRead.model_config = ConfigDict(
    from_attributes=True,
    extra="ignore",
    json_schema_extra={
        "example": {
            "id": 1,
            "rule_id": "R001",
            "name": "Jupiter in Ketu Nakshatra",
            "description": "Market weakens when Jupiter transits Ketu Nakshatra",
            "confidence": 0.9,
            "enabled": True,
            "conditions": [
                {"id": 1, "rule_id": 1, "planet": "jupiter", "relation": "in_nakshatra_owned_by", "target": "ketu"}
            ],
            "outcomes": [
                {"id": 1, "rule_id": 1, "sector_code": "EQUITY", "effect": "Bearish", "weight": 1.0}
            ],
            "created_at": "2025-10-21T12:00:00Z",
            "updated_at": "2025-10-21T12:00:00Z"
        }
    },
)



# ---------------------------------------------------------------------
# Evaluation / Event schemas
# ---------------------------------------------------------------------
class EvaluateRequest(BaseModel):
    """Payload for /evaluate endpoint."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class EventResult(BaseModel):
    """Represents an event triggered by a rule evaluation."""
    rule_id: str
    date: str
    sector: str
    effect: str
    weight: float
    confidence: float

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CorrelationResult(BaseModel):
    """Output structure for correlation analysis results."""
    ticker: str
    lookahead_days: List[int]
    aggregate: dict
    per_rule: dict

    model_config = ConfigDict(from_attributes=True, extra="ignore")
