from datetime import timedelta, date
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.db.models_analysis import RuleEvent, DurationType, EventSubtype
from app.core.db.models import Rule
from app.core.astro.factories.provider_factory import get_provider as get_astro_provider
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl

import logging
logger = logging.getLogger("astro.eventgen")

class EventGeneratorService:
    """
    Evaluate each rule across a date range using the astro provider and rules engine.
    Detect periods/points, generate RuleEvent entries, and persist them.
    """

    def __init__(self, db_session: Session, astro_provider_name: str = "swisseph"):
        self.db = db_session
        self.astro_provider_name = astro_provider_name
        self.astro = get_astro_provider(astro_provider_name)
        self.rules_engine = RulesEngineImpl(self.astro)

    @staticmethod
    def _daterange(start_date: date, end_date: date):
        current = start_date
        while current <= end_date:
            yield current
            current += timedelta(days=1)

    def generate_for_rule(
        self,
        rule_id: int,
        start_date: date,
        end_date: date,
        provider: Optional[str] = None,
        overwrite: bool = False,
    ) -> List[RuleEvent]:
        """Generate and persist RuleEvent rows for the specified rule."""
        logger.info(f"🚀 Starting generation for rule_id={rule_id}, "
                    f"provider={provider}, overwrite={overwrite}")
        if provider:
            self.astro = get_astro_provider(provider)
            self.rules_engine = RulesEngineImpl(self.astro)
            self.astro_provider_name = provider

        rule = self.db.query(Rule).filter(Rule.id == rule_id).one_or_none()
        if not rule:
            logger.error(f"❌ Rule {rule_id} not found in database")
            raise ValueError(f"Rule {rule_id} not found")

        if overwrite:
            logger.info(f"🧹 Deleting existing events overlapping {start_date} → {end_date}")
            q = (
                self.db.query(RuleEvent)
                .filter(RuleEvent.rule_id == rule.id)
                .filter(RuleEvent.start_date <= end_date)
                .filter((RuleEvent.end_date == None) | (RuleEvent.end_date >= start_date))
            )
            deleted = q.delete(synchronize_session="fetch")
            self.db.commit()
            logger.info(f"🗑️  Deleted {deleted} existing events")

        events_to_create = []
        active_start = None
        last_true = None
        context_last = None

        for dt in self._daterange(start_date, end_date):
            try:
                result = self.rules_engine.evaluate_rule(rule, dt)
                if isinstance(result, tuple):
                    is_true, context = result
                else:
                    is_true, context = result, None
            except Exception:
                logger.exception(f"⚠️  Error evaluating rule {rule_id} on {dt}: {e}")
                continue

            if is_true and active_start is None:
                active_start = dt
                last_true = dt
                context_last = context
                logger.debug(f"🔹 Active start detected at {active_start}")
            elif is_true:
                last_true = dt
                context_last = context
            elif not is_true and active_start is not None:
                duration = (last_true - active_start).days + 1
                subtype = (
                    EventSubtype.instant
                    if duration == 1
                    else EventSubtype.transient if duration <= 3 else EventSubtype.period
                )
                evt = RuleEvent(
                    rule_id=rule_id,
                    start_date=active_start,
                    end_date=last_true,
                    duration_type=DurationType.interval if duration > 1 else DurationType.point,
                    event_subtype=subtype,
                    provider=self.astro_provider_name,
                    metadata_json=context_last or {},
                )
                events_to_create.append(evt)
                logger.info(f"🧩 Added event: {active_start}–{last_true}, subtype={subtype.name}")
                active_start = None
                last_true = None
                context_last = None

        # If still active till end of range
        if active_start is not None:
            duration = (end_date - active_start).days + 1
            subtype = (
                EventSubtype.instant
                if duration == 1
                else EventSubtype.transient if duration <= 3 else EventSubtype.period
            )
            evt = RuleEvent(
                rule_id=rule_id,
                start_date=active_start,
                end_date=end_date,
                duration_type=DurationType.interval if duration > 1 else DurationType.point,
                event_subtype=subtype,
                provider=self.astro_provider_name,
                metadata_json=context_last or {},
            )
            events_to_create.append(evt)

        if events_to_create:
            self.db.add_all(events_to_create)
            self.db.commit()
            logger.info(f"💾 Persisted {len(events_to_create)} events for rule_id={rule_id}")
            for e in events_to_create:
                self.db.refresh(e)
        else:
            logger.warning(f"⚠️ No events detected for rule_id={rule_id}")

        return events_to_create
