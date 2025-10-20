# backend/app/core/astro/providers/stub_provider.py
from datetime import datetime
import math
from core.astro.interfaces.i_astro_provider import IAstroProvider

class StubProvider(IAstroProvider):
    """Deterministic stub provider for tests and local development."""

    def __init__(self):
        # optional config
        pass

    def longitude(self, planet: str, when: datetime) -> float:
        base = sum(ord(c) for c in planet.lower()) % 360
        days = (when.date() - datetime(2000, 1, 1).date()).days
        motion = {
            "sun": 0.9856, "moon": 13.1764, "mercury": 4.0923,
            "venus": 1.2, "mars": 0.524, "jupiter": 0.083,
            "saturn": 0.033, "rahu": -0.03, "ketu": 0.03
        }
        m = motion.get(planet.lower(), 0.1)
        return (base + days * m) % 360

    def nakshatra_index(self, longitude_deg: float) -> int:
        return int(math.floor((longitude_deg % 360.0) / (360.0 / 27.0)))

    def nakshatra_owner(self, nak_idx: int) -> str:
        owners = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter"]
        return owners[nak_idx % len(owners)]

    def angular_distance(self, a: float, b: float) -> float:
        return abs((a - b + 180) % 360 - 180)
