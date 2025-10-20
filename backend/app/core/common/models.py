# backend/app/core/common/models.py
"""
Data models for Astro Rules Engine
----------------------------------
Clean, Pydantic v2–compatible SQLModel definitions.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from pydantic import ConfigDict


# --------------------------------------------------------------------
# Rule storage model
# --------------------------------------------------------------------
class RuleModel(SQLModel, table=True):
    """
    Stores each astrological rule definition with its
    serialized conditions and outcomes.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: str = Field(index=True, unique=True, description="Unique rule identifier")
    name: str = Field(description="Human-readable rule name")
    description: Optional[str] = Field(default=None, description="Detailed rule description")

    # Serialized JSON
    conditions_json: str = Field(description="JSON-serialized list of Condition objects")
    outcomes_json: str = Field(description="JSON-serialized list of Outcome objects")

    enabled: bool = Field(default=True, description="Whether the rule is active")
    confidence: float = Field(default=1.0, description="Confidence weight 0–1")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp (UTC)")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp (UTC)")

    # --- Pydantic v2 config ---
    model_config = ConfigDict(
        from_attributes=True,   # ORM-friendly
        extra="ignore",          # ignore unexpected fields
        json_schema_extra={
            "example": {
                "rule_id": "R001",
                "name": "Jupiter in Ketu Nakshatra",
                "description": "Market weakens when Jupiter transits Ketu Nakshatra",
                "conditions_json": "[{...}]",
                "outcomes_json": "[{...}]",
                "enabled": True,
                "confidence": 0.85,
            }
        },
    )


# --------------------------------------------------------------------
# Backtest / Correlation results model
# --------------------------------------------------------------------
class BacktestRun(SQLModel, table=True):
    """
    Stores results of correlation / backtest analyses for reproducibility.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Run label or identifier")
    ticker: str = Field(description="Market ticker used for analysis")

    params_json: str = Field(description="Serialized run parameters")
    stats_json: str = Field(description="Aggregated statistics JSON")
    events_json: Optional[str] = Field(default=None, description="Detailed event-level results")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Run creation timestamp (UTC)")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# --------------------------------------------------------------------
# Optional: helper metadata model (future extension)
# --------------------------------------------------------------------
class SectorModel(SQLModel, table=True):
    """
    Reference table for sectors / categories used in rule outcomes.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, description="Short sector code, e.g., BANK, METAL")
    name: str = Field(description="Full sector name")
    description: Optional[str] = Field(default=None, description="Optional notes")

    model_config = ConfigDict(from_attributes=True, extra="ignore")
