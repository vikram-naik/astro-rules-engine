from datetime import datetime, date
import enum

from sqlalchemy import (
    Column,
    Integer,
    Date,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.core.db.db import Base


class DurationType(enum.Enum):
    point = "point"
    interval = "interval"


class EventSubtype(enum.Enum):
    instant = "instant"
    period = "period"
    transient = "transient"


class RuleEvent(Base):
    __tablename__ = "rule_events"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rule.id", ondelete="CASCADE"), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    duration_type = Column(SAEnum(DurationType), nullable=False, default=DurationType.point)
    event_subtype = Column(SAEnum(EventSubtype), nullable=True)

    provider = Column(String(64), nullable=False, default="swisseph")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rule = relationship("Rule", back_populates="events", lazy="joined")

    def to_dict(self):
        return dict(
            id=self.id,
            rule_id=self.rule_id,
            start_date=self.start_date.isoformat() if isinstance(self.start_date, date) else self.start_date,
            end_date=self.end_date.isoformat() if isinstance(self.end_date, date) else self.end_date,
            duration_type=self.duration_type.name if self.duration_type else None,
            event_subtype=self.event_subtype.name if self.event_subtype else None,
            provider=self.provider,
            metadata_json=self.metadata_json,
            created_at=self.created_at.isoformat() if self.created_at else None,
        )
