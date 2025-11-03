import json
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple
import logging

from app.core.db.models_ephemeris import EphemerisCache
from app.core.db import SessionLocal
from app.core.astro.factories.provider_factory import get_provider
from app.core.db.astro_config import AstroConfig
from app.core.db.enums import AyanamsaMode, Planet, Sign
from app.core.common.config import DEFAULT_REFERENCE_TIME

logger = logging.getLogger("astro.ephemeris")

COMBUSTION_ORBS = {
    Planet.moon: 12,
    Planet.mars: 17,
    Planet.mercury: 14,
    Planet.jupiter: 11,
    Planet.venus: 10,
    Planet.saturn: 15,
}


def normalize_angle(a: float) -> float:
    a = a % 360.0
    return a + 360.0 if a < 0 else a


def deg_to_sign_index(lon: float) -> int:
    return int(normalize_angle(lon) // 30)


def sign_and_dms(lon: float) -> Tuple[int, Dict[str, int], float]:
    lon = normalize_angle(lon)
    s = int(lon // 30)
    rel = lon - s * 30
    d = int(rel)
    m = int((rel - d) * 60)
    s2 = int(round(((rel - d) * 60 - m) * 60))
    if s2 >= 60:
        s2 -= 60
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return s, {"deg": d, "min": m, "sec": s2}, rel


def estimate_speed(provider, planet: Planet, when_utc: datetime, dt_s: int = 3600) -> float:
    dt = timedelta(seconds=dt_s)
    lon1 = provider.longitude(planet, when_utc - dt)
    lon2 = provider.longitude(planet, when_utc + dt)
    diff = (normalize_angle(lon2) - normalize_angle(lon1))
    if diff > 180:
        diff -= 360
    if diff < -180:
        diff += 360
    return diff / (2 * dt_s) * 86400.0  # deg/day


def find_ingress(provider, planet, start_l, end_l, boundary, max_iter=40) -> Optional[datetime]:
    s_u = start_l.astimezone(ZoneInfo("UTC"))
    e_u = end_l.astimezone(ZoneInfo("UTC"))

    def f(tu):
        lon = normalize_angle(provider.longitude(planet, tu))
        d = lon - boundary
        while d <= -180:
            d += 360
        while d > 180:
            d -= 360
        return d

    f0, f1 = f(s_u), f(e_u)
    if f0 * f1 > 0:
        return None
    a, b, fa, fb = s_u, e_u, f0, f1
    for _ in range(max_iter):
        m = a + (b - a) / 2
        fm = f(m)
        if abs(fm) < 1e-6:
            return m.astimezone(start_l.tzinfo)
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return (a + (b - a) / 2).astimezone(start_l.tzinfo)


# ---------------------------------------------------------------
# Dignity Rules
# ---------------------------------------------------------------
DIGNITY_RULES = {
    Planet.sun: {
        "exalt": Sign.aries,
        "exalt_deg": 10,
        "debil": Sign.libra,
        "debil_deg": 10,
        "mt": (Sign.leo, 0, 20),
    },
    Planet.moon: {
        "exalt": Sign.taurus,
        "exalt_deg": 3,
        "debil": Sign.scorpio,
        "debil_deg": 3,
        "mt": (Sign.taurus, 4, 30),
    },
    Planet.mars: {
        "exalt": Sign.capricorn,
        "exalt_deg": 28,
        "debil": Sign.cancer,
        "debil_deg": 28,
        "mt": (Sign.aries, 0, 12),
    },
    Planet.mercury: {
        "exalt": Sign.virgo,
        "exalt_deg": 15,
        "debil": Sign.pisces,
        "debil_deg": 15,
        "mt": (Sign.virgo, 16, 20),
    },
    Planet.jupiter: {
        "exalt": Sign.cancer,
        "exalt_deg": 5,
        "debil": Sign.capricorn,
        "debil_deg": 5,
        "mt": (Sign.sagittarius, 0, 10),
    },
    Planet.venus: {
        "exalt": Sign.pisces,
        "exalt_deg": 27,
        "debil": Sign.virgo,
        "debil_deg": 27,
        "mt": (Sign.libra, 0, 15),
    },
    Planet.saturn: {
        "exalt": Sign.libra,
        "exalt_deg": 20,
        "debil": Sign.aries,
        "debil_deg": 20,
        "mt": (Sign.aquarius, 0, 20),
    },
    Planet.rahu: {
        "exalt": Sign.taurus,
        "debil": Sign.scorpio,
        "mt": (Sign.aquarius, 0, 30),
    },
    Planet.ketu: {
        "exalt": Sign.scorpio,
        "debil": Sign.taurus,
        "mt": (Sign.leo, 0, 30),
    },
}


def compute_dignity(planet: Planet, sign_enum: Sign, rel_deg: float) -> Optional[str]:
    """Return 'Ex', 'Db', 'MT', or None."""
    rules = DIGNITY_RULES.get(planet)
    if not rules:
        return None

    # Exaltation
    if rules.get("exalt") == sign_enum:
        return "Ex"

    # Debilitation
    if rules.get("debil") == sign_enum:
        return "Db"

    # Moolatrikona
    mt_rule = rules.get("mt")
    if mt_rule and mt_rule[0] == sign_enum:
        start, end = mt_rule[1], mt_rule[2]
        if start <= rel_deg <= end:
            return "MT"

    return None


# ---------------------------------------------------------------
# Ephemeris Service
# ---------------------------------------------------------------
class EphemerisService:
    def __init__(self, cache_session=None):
        self.cache = cache_session or SessionLocal()

    def get_providers(self) -> List[Dict[str, str]]:
        return [
            {"id": "skyfield", "label": "Skyfield"},
            {"id": "swisseph", "label": "Swiss Ephemeris"},
        ]

    def compute_matrix(
        self,
        provider_id: str,
        ayanamsa: AyanamsaMode,
        tz_name: str,
        lat: float,
        lon: float,
        alt: int,
        start_date: date,
        reference_time: time,
        force_refresh=False,
        max_workers: int = 2,
        node_mode: str = "mean",
    ) -> Dict[str, Any]:
        # ---- Setup ----
        cfg = self.cache.query(AstroConfig).get("global")
        if not cfg:
            logger.warning("⚠️ AstroConfig missing 'global' row – using defaults.")
        provider = get_provider(
            provider_id,
            ayanamsa_mode=ayanamsa,
            fresh=False,
            location={"lon": lon, "lat": lat, "alt": alt},
            tz_name=tz_name,
        )

        if not reference_time:
            try:
                h, m, s = [int(x) for x in DEFAULT_REFERENCE_TIME.split(":")]
                reference_time = time(h, m, s)
            except Exception:
                reference_time = time(0, 0, 0)

        dates = [start_date + timedelta(days=i) for i in range(7)]
        ref_iso = reference_time.isoformat()

        if force_refresh:
            self.cache.query(EphemerisCache).filter_by(
                provider=provider_id,
                ayanamsa=ayanamsa,
                tz_name=tz_name,
                lat=lat,
                lon=lon,
                reference_time=ref_iso,
            ).delete()
            self.cache.commit()

        existing = self.cache.query(EphemerisCache).filter(
            EphemerisCache.provider == provider_id,
            EphemerisCache.ayanamsa == ayanamsa,
            EphemerisCache.tz_name == tz_name,
            EphemerisCache.lat == lat,
            EphemerisCache.lon == lon,
            EphemerisCache.reference_time == ref_iso,
            EphemerisCache.date.in_([d.isoformat() for d in dates]),
        ).all()
        cache_map = {(r.date, Planet[r.planet]): r for r in existing}

        # ---- Compute missing snapshots ----
        tasks = [(d, p) for d in dates for p in Planet if (d.isoformat(), p) not in cache_map]
        computed = {}
        if tasks:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = {
                    ex.submit(
                        self._compute_snapshot,
                        provider,
                        p,
                        d,
                        reference_time,
                        tz_name,
                        ayanamsa,
                        node_mode,
                    ): (d, p)
                    for d, p in tasks
                }
                for f in as_completed(futs):
                    d, p = futs[f]
                    try:
                        result = f.result()
                        computed[(d, p)] = result
                    except Exception as e:
                        computed[(d, p)] = {"error": str(e)}
                        logger.error(f"❌ Failed {p} for {d}: {e}", exc_info=True)

        for (d, p), snap in computed.items():
            if "error" in snap:
                continue
            row = EphemerisCache(
                provider=provider_id,
                ayanamsa=ayanamsa.name,
                tz_name=tz_name,
                lat=lat,
                lon=lon,
                alt=alt,
                reference_time=ref_iso,
                date=d.isoformat(),
                planet=p.name,
                longitude=snap["longitude"],
                longitude_dms=json.dumps(snap["longitude_dms"]),
                speed=snap["speed"],
                is_retrograde=int(snap["is_retrograde"]),
                is_stationary=int(snap["is_stationary"]),
                dignity=snap.get("dignity"),
                combust=int(snap["combust"]),
            )
            self.cache.add(row)
        self.cache.commit()

        # ---- Detect sign transitions ----
        transitions: dict[tuple[str, str], dict] = {}
        for p in Planet:
            for i in range(len(dates) - 1):
                d1, d2 = dates[i], dates[i + 1]
                r1 = computed.get((d1, p)) or cache_map.get((d1.isoformat(), p))
                r2 = computed.get((d2, p)) or cache_map.get((d2.isoformat(), p))
                if not r1 or not r2:
                    continue

                lon1 = r1["longitude"] if isinstance(r1, dict) else r1.longitude
                lon2 = r2["longitude"] if isinstance(r2, dict) else r2.longitude
                s1, _, _ = sign_and_dms(lon1)
                s2, _, _ = sign_and_dms(lon2)

                if s1 != s2:
                    boundary = 30 * s2
                    when_l = datetime.combine(d1, reference_time).replace(tzinfo=ZoneInfo(tz_name))
                    when_next = when_l + timedelta(days=1)
                    ingress_dt = find_ingress(provider, p, when_l, when_next, boundary)
                    if ingress_dt:
                        transitions[(d2.isoformat(), p.name)] = {
                            "transition_from": list(Sign)[s1].name,
                            "transition_to": list(Sign)[s2].name,
                            "transition_time_local": ingress_dt.strftime("%H:%M %Z"),
                        }

        # ---- Build output ----
        rows = []
        for d in dates:
            ds = d.isoformat()
            cells = {}
            for p in Planet:
                r = cache_map.get((ds, p)) or self.cache.query(EphemerisCache).filter_by(
                    provider=provider_id,
                    ayanamsa=ayanamsa.name,
                    tz_name=tz_name,
                    lat=lat,
                    lon=lon,
                    reference_time=ref_iso,
                    date=ds,
                    planet=p.name,
                ).first()
                if not r:
                    continue
                cell = r.to_dict()
                s_idx, dms, rel = sign_and_dms(r.longitude)
                sign_enum = list(Sign)[s_idx]
                dignity = compute_dignity(p, sign_enum, rel)
                cell["sign"] = sign_enum.name
                cell["dignity"] = dignity
                key = (ds, p.name)
                if key in transitions:
                    cell.update(transitions[key])
                else:
                    cell.update(
                        {
                            "transition_from": None,
                            "transition_to": None,
                            "transition_time_local": None,
                        }
                    )
                cells[p.name] = cell
            rows.append({"date": ds, "cells": cells})

        meta = {
            "provider": provider_id,
            "ayanamsa": ayanamsa.name,
            "location": {"lat": lat, "lon": lon, "alt": alt},
            "tz_name": tz_name,
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=6)).isoformat(),
            "reference_time": ref_iso,
        }

        return {"meta": meta, "planets": Planet._member_names_, "rows": rows}

    def _compute_snapshot(
        self, provider, planet: Planet, d: date, ref_t: time, tz: str, ayanamsa: str, node_mode: str
    ) -> Dict[str, Any]:
        when_l = datetime.combine(d, ref_t).replace(tzinfo=ZoneInfo(tz))
        when_u = when_l.astimezone(ZoneInfo("UTC"))
        # lon = provider.longitude(planet, when_u)
        # to fix the moon bug - we are passing the when_l
        lon = provider.longitude(planet, when_l)
        sp = estimate_speed(provider, planet, when_l, 1800 if planet == Planet.moon else 3600)
        isr = sp < -1e-6
        iss = abs(sp) < 1e-5
        s_idx, dms, rel = sign_and_dms(lon)
        combust = False
        if planet in COMBUSTION_ORBS:
            sun_lon = provider.longitude(Planet.sun, when_u)
            ang = abs(normalize_angle(lon - sun_lon))
            ang = ang if ang <= 180 else 360 - ang
            combust = ang <= COMBUSTION_ORBS[planet]

        sign_enum = list(Sign)[s_idx]
        dignity = compute_dignity(planet, sign_enum, rel)
        return {
            "longitude": lon,
            "longitude_dms": dms,
            "speed": sp,
            "is_retrograde": isr,
            "is_stationary": iss,
            "dignity": dignity,
            "combust": combust,
            "sign": sign_enum.name,
        }
