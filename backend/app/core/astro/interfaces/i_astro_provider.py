# backend/app/core/astro/interfaces/i_astro_provider.py
from abc import ABC, abstractmethod
from datetime import datetime

class IAstroProvider(ABC):
    """Interface for planetary data providers."""

    @abstractmethod
    def longitude(self, planet: str, when: datetime) -> float:
        """Return ecliptic longitude in degrees for planet at given datetime."""
        raise NotImplementedError

    @abstractmethod
    def nakshatra_index(self, longitude_deg: float) -> int:
        """Return nakshatra index (0..26) for given longitude."""
        raise NotImplementedError

    @abstractmethod
    def nakshatra_owner(self, nak_idx: int) -> str:
        """Return owner name for a given nakshatra index."""
        raise NotImplementedError

    @abstractmethod
    def angular_distance(self, a: float, b: float) -> float:
        """Return shortest angular distance in degrees between angles a and b."""
        raise NotImplementedError
    
    @abstractmethod
    def is_retrograde(self, planet: str, when: datetime) -> bool:
        """Return True if planet is retrograde at the given time."""
        raise NotImplementedError
