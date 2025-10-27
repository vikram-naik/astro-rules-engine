# app/core/astro/providers/_mixins.py
from datetime import datetime as dt, timezone

# ✅ correct: assign tz_utc to the instance, not the class
tz_utc = timezone.utc

class AstroTimeMixin:
    def _normalize_when_utc(self, when):
        """Normalize date/datetime → UTC datetime using self.tz (if any)."""
        if isinstance(when, dt):
            if when.tzinfo is None:
                when = when.replace(tzinfo=getattr(self, "tz", tz_utc))
            return when.astimezone(tz_utc)
        else:
            # assume date
            when_local = dt(when.year, when.month, when.day, 0, 0, 0,
                            tzinfo=getattr(self, "tz", tz_utc))
            return when_local.astimezone(tz_utc)
