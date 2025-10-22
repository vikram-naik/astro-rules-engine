# app/core/common/models.py
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import  relationship
from app.core.db.db import Base

class Sector(Base):
    __tablename__ = "sector"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)

class Rule(Base):
    __tablename__ = "rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    enabled = Column(Boolean, default=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Master–detail relationships
    conditions = relationship(
        "Condition",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    outcomes = relationship(
        "Outcome",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    # add: one-to-many relationship to persisted events
    events = relationship(
        "RuleEvent",
        cascade="all, delete-orphan",
        lazy="select",   # load on access (safer for large result sets)
    )


class Condition(Base):
    __tablename__ = "condition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("rule.id", ondelete="CASCADE"), nullable=False)
    planet = Column(String)
    relation = Column(String)
    target = Column(String)
    orb = Column(Float)
    value = Column(Float)

    rule = relationship("Rule", back_populates="conditions")


class Outcome(Base):
    __tablename__ = "outcome"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("rule.id", ondelete="CASCADE"), nullable=False)
    sector_id = Column(Integer, ForeignKey("sector.id", ondelete="SET NULL"))
    effect = Column(String)
    weight = Column(Float, default=1.0)

    # relationships
    rule = relationship("Rule", back_populates="outcomes")
    sector = relationship("Sector")  # simple reference, no backref
