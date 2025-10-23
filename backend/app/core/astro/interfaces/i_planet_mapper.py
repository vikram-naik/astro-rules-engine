# app/core/astro/interfaces/i_planet_mapper.py
from abc import ABC, abstractmethod
from app.core.db.enums import Planet


class IPlanetMapper(ABC):
    """Maps canonical Planet enums to provider-specific identifiers."""

    @abstractmethod
    def resolve(self, planet: Planet) -> str:
        """Return provider-specific key for given Planet."""
        pass
