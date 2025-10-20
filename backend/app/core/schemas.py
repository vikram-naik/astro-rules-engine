from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class Relation(str, Enum):
    in_nakshatra_owned_by = "in_nakshatra_owned_by"
    conjunct_with = "conjunct_with"
    aspect_with = "aspect_with"
    in_sign = "in_sign"
    in_axis = "in_axis"
    in_house_relative_to = "in_house_relative_to"


class Condition(BaseModel):
    planet: str
    relation: Relation
    target: Optional[str] = None
    value: Optional[float] = None
    orb: Optional[float] = 5.0


class OutcomeEffect(str, Enum):
    Bullish = "Bullish"
    Bearish = "Bearish"
    Neutral = "Neutral"


class Outcome(BaseModel):
    sector_code: str
    effect: OutcomeEffect
    weight: Optional[float] = 1.0


class RuleCreate(BaseModel):
    rule_id: str
    name: str
    description: Optional[str] = None
    conditions: List[Condition]
    outcomes: List[Outcome]
    enabled: Optional[bool] = True
    confidence: Optional[float] = 0.8


class RuleRead(BaseModel):
    rule_id: str
    name: str
    description: Optional[str]
    conditions: List[Condition]
    outcomes: List[Outcome]
    enabled: bool
    confidence: float


class EvaluateRequest(BaseModel):
    start_date: str
    end_date: str