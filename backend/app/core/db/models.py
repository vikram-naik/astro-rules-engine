# app/core/common/models.py
from datetime import datetime, UTC
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship, backref
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
    name = Column(String, nullable=False)
    description = Column(String)
    enabled = Column(Boolean, default=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Each rule has one or more top-level condition groups
    condition_groups = relationship(
        "ConditionGroup",
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
        lazy="select",
    )


class ConditionGroup(Base):
    """
    Represents a logical grouping of conditions.
    Supports nesting via parent_group_id.
    operator: "AND" | "OR"
    order: integer for deterministic ordering within a rule.
    """
    __tablename__ = "condition_group"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("rule.id", ondelete="CASCADE"), nullable=False)
    parent_group_id = Column(Integer, ForeignKey("condition_group.id", ondelete="CASCADE"), nullable=True)

    operator = Column(String, default="AND", nullable=False)  # "AND" or "OR"
    order = Column(Integer, default=0)

    # relationships
    rule = relationship("Rule", back_populates="condition_groups")

    parent_group = relationship(
        "ConditionGroup",
        remote_side=[id],
        backref=backref("subgroups", cascade="all, delete-orphan"),
    )

    conditions = relationship(
        "Condition",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class Condition(Base):
    __tablename__ = "condition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("condition_group.id", ondelete="CASCADE"), nullable=False)

    planet = Column(String)
    relation = Column(String)
    target = Column(String)
    orb = Column(Float)
    value = Column(Float)

    group = relationship("ConditionGroup", back_populates="conditions")


class Outcome(Base):
    __tablename__ = "outcome"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("rule.id", ondelete="CASCADE"), nullable=False)
    sector_id = Column(Integer, ForeignKey("sector.id", ondelete="SET NULL"))
    effect = Column(String)
    weight = Column(Float, default=1.0)

    rule = relationship("Rule", back_populates="outcomes")
    sector = relationship("Sector")  # simple reference, no backref
