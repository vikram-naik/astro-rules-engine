import math
from datetime import datetime


# Try to import pyswisseph; fall back to a deterministic stub
HAS_SW = False
try:
    import swisseph as swe
    HAS_SW = True
except Exception:
    HAS_SW = False


class AstroProvider:
    PLANETS = ["sun","moon","mercury","venus","mars","jupiter","saturn","rahu","ketu"]


    def __init__(self, use_sidereal=True):
        self.use_sidereal = use_sidereal


    def longitude(self, planet: str, when: datetime) -> float:
        planet = planet.lower()
        if HAS_SW:
            return self._sw_lon(planet, when)
        return self._stub_lon(planet, when)


    def _stub_lon(self, planet: str, when: datetime) -> float:
        base = sum(ord(c) for c in planet) % 360
        days = (when.date() - datetime(2000,1,1).date()).days
        motion = {
            "sun": 0.9856, "moon": 13.1764, "mercury": 4.0923, "venus": 1.2,
            "mars": 0.524, "jupiter": 0.083, "saturn": 0.033, "rahu": -0.03, "ketu": 0.03
        }
        m = motion.get(planet, 0.1)
        return (base + days * m) % 360


    def _sw_lon(self, planet: str, when: datetime) -> float:
        body_map = {
            'sun': swe.SUN, 'moon': swe.MOON, 'mercury': swe.MERCURY, 'venus': swe.VENUS,
            'mars': swe.MARS, 'jupiter': swe.JUPITER, 'saturn': swe.SATURN
        }
        if planet in ('rahu', 'ketu'):
            jd = swe.julday(when.year, when.month, when.day, when.hour + when.minute/60.0)
            lon = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
        if planet == 'ketu':
            lon = (lon + 180) % 360
            return lon % 360
        key = body_map.get(planet)
        if key is None:
            return self._stub_lon(planet, when)
        jd = swe.julday(when.year, when.month, when.day, when.hour + when.minute/60.0)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        lon = swe.calc_ut(jd, key)[0][0]
        return lon % 360


    def nakshatra_index(self, longitude_deg: float) -> int:
        return int(math.floor((longitude_deg % 360.0) / (360.0/27.0)))


    def nakshatra_owner(self, nak_idx: int) -> str:
        owners = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter"]
        return owners[nak_idx % len(owners)]


    def angular_distance(self, a: float, b: float) -> float:
        return abs((a-b+180)%360 - 180)