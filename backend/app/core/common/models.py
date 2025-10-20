from typing import Optional
from sqlmodel import SQLModel, Field


class Sector(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str
    description: Optional[str] = None


class RuleModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: str = Field(index=True, unique=True)
    name: str
    description: Optional[str] = None
    enabled: bool = True
    confidence: float = 0.8
    conditions_json: Optional[str] = None
    outcomes_json: Optional[str] = None