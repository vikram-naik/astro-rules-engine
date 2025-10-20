# backend/app/core/common/schemas.py
"""
Schemas for Astro Rules Engine
------------------------------
Defines Pydantic v2 models used for input/output and internal data structures.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------
# Enums for controlled vocabulary
# ---------------------------------------------------------------------
class Relation(str, Enum):
    """Possible astrological relationships / rule conditions."""
    in_nakshatra_owned_by = "in_nakshatra_owned_by"
    conjunct_with = "conjunct_with"
    in_axis = "in_axis"
    aspect_with = "aspect_with"
    in_sign = "in_sign"
    in_house_relative_to = "in_house_relative_to"


class OutcomeEffect(str, Enum):
    """Possible rule effects on a sector or market."""
    Bullish = "Bullish"
    Bearish = "Bearish"
    Neutral = "Neutral"


# ---------------------------------------------------------------------
# Core condition and outcome schemas
# ---------------------------------------------------------------------
class Condition(BaseModel):
    """A single condition defining a planetary configuration."""
    planet: str = Field(..., description="Name of planet")
    relation: Relation = Field(..., description="Type of relation or aspect")
    target: Optional[str] = Field(default=None, description="Target planet or nakshatra owner")
    orb: Optional[float] = Field(default=5.0, description="Orb of influence (degrees)")
    value: Optional[float] = Field(default=None, description="Optional numeric value (e.g., aspect angle)")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class Outcome(BaseModel):
    """A single predicted outcome of a rule."""
    sector_code: str = Field(..., description="Sector or asset impacted (e.g., BANK, METAL, EQUITY)")
    effect: OutcomeEffect = Field(..., description="Expected direction or sentiment")
    weight: float = Field(default=1.0, description="Weight of this outcome (relative importance)")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ---------------------------------------------------------------------
# High-level rule schemas
# ---------------------------------------------------------------------
class RuleBase(BaseModel):
    """Common base fields shared by create/update/read rule schemas."""
    rule_id: Optional[str] = Field(default=None, description="Unique identifier of rule")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(default=None, description="Detailed description")
    confidence: float = Field(default=1.0, description="Confidence level (0–1)")
    enabled: bool = Field(default=True, description="Whether rule is active")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class RuleCreate(RuleBase):
    """Schema used for creating new rules."""
    conditions: List[Condition] = Field(..., description="List of rule conditions")
    outcomes: List[Outcome] = Field(..., description="List of rule outcomes")


class RuleRead(RuleBase):
    """Schema for reading rules from the database."""
    id: Optional[int] = Field(default=None)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    conditions: Optional[List[Condition]] = None
    outcomes: Optional[List[Outcome]] = None


class RuleUpdate(BaseModel):
    """Partial update for existing rules."""
    name: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[float] = None
    enabled: Optional[bool] = None
    conditions: Optional[List[Condition]] = None
    outcomes: Optional[List[Outcome]] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


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
