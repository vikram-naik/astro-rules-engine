# app/core/common/schemas.py
from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------
# Evaluation / Event schemas (retained for evaluation endpoints)
# ---------------------------------------------------------------------
class EvaluateRequest(BaseModel):
    """Payload for /evaluate endpoint."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class EventResult(BaseModel):
    """Represents an event triggered by a rule evaluation."""
    rule_id: int
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
    aggregate: Dict
    per_rule: Dict

    model_config = ConfigDict(from_attributes=True, extra="ignore")
