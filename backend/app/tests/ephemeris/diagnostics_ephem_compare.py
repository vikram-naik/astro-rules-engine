# diagnostics_ephem_compare.py
from datetime import datetime
from zoneinfo import ZoneInfo

# import your providers/factory
from app.core.astro.factories.provider_factory import get_provider
import swisseph as swe  # you already have this in your project


def test_diagnostics_ephem_compare():
    tz = "Asia/Kolkata"
    lat, lon, alt = 20.45, 72.57, 0
    dt_local = datetime(1976, 2, 28, 1, 58, 57, tzinfo=ZoneInfo(tz))

    # Get a Skyfield provider (your class)
    sky = get_provider("skyfield", ayanamsa_mode=None, location={"lon": lon, "lat": lat, "alt": alt}, tz_name=tz, fresh=True)
    sky.configure({"lon": lon, "lat": lat, "alt": alt}, tz_name=tz)

    # Get a SwissEphem provider
    sweprov = get_provider("swisseph", ayanamsa_mode=None, location={"lon": lon, "lat": lat, "alt": alt}, tz_name=tz, fresh=True)
    sweprov.configure({"lon": lon, "lat": lat, "alt": alt}, tz_name=tz)

    # 1) Tropical longitude via Skyfield (compute without sidereal correction)
    #    — call skyfield longitude but force tropical by bypassing ayanamsa
    tropical_lon_sky = sky.longitude("jupiter", dt_local) if sky.ayanamsa_mode == None else None
    # we will get tropical by temporarily using ayanamsa_mode = tropical if provider supports it
    # safer: compute via Skyfield internals directly (assumes sky has attribute plan ets & timescale)
    try:
        # get pure tropical by constructing ts and reading frame without ayanamsa correction
        from skyfield.api import load, wgs84
        ts = sky.timescale
        t = ts.utc(dt_local.astimezone(ZoneInfo("UTC")))
        earth = sky.planets["earth"]
        body = sky.planets["jupiter barycenter"] if "jupiter barycenter" in sky.planets else sky.planets["jupiter"]
        ast = (earth + wgs84.latlon(lat, lon, alt)).at(t).observe(body).apparent()
        trop_lat, trop_lon, _ = ast.frame_latlon(__import__("skyfield.framelib", fromlist=["ecliptic_frame"]).ecliptic_frame)
        tropical_lon = trop_lon.degrees % 360.0
    except Exception as e:
        tropical_lon = None
        print("Skyfield tropical compute failed:", e)

    # 2) Ayanamsa from your Skyfield function (what your code uses)
    #    compute what sky._ayanamsa_deg returns for JD TT
    jd_tt = float(t.tt)
    sky_ay = None
    try:
        if hasattr(sky, "_ayanamsa_deg"):
            sky_ay = sky._ayanamsa_deg(float(t.tt))
    except Exception as e:
        print("Skyfield ayanamsa compute failed:", e)

    # 3) SwissEphem's ayanamsa (use swe.get_ayanamsa or compute by difference)
    #    Ensure SID mode is Lahiri
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    when_utc = dt_local.astimezone(ZoneInfo("UTC"))
    jd_ut = swe.julday(when_utc.year, when_utc.month, when_utc.day,
                    when_utc.hour + when_utc.minute/60.0 + when_utc.second/3600.0)

    # compute tropical & sidereal Jupiter via swe.calc_ut
    flags = swe.FLG_SWIEPH
    res_t, _ = swe.calc_ut(jd_ut, swe.JUPITER, flags)        # tropical
    res_s, _ = swe.calc_ut(jd_ut, swe.JUPITER, flags | swe.FLG_SIDEREAL)  # sidereal (Lahiri)
    swe_trop = float(res_t[0]) % 360.0
    swe_sid  = float(res_s[0]) % 360.0
    # SwissEphem ayanamsa = tropical - sidereal (wrapped)
    swe_ay = (swe_trop - swe_sid) % 360.0

    print("DT local:", dt_local.isoformat())
    print("JD UT:", jd_ut)
    print("Skyfield tropical (computed):", tropical_lon)
    print("Skyfield ayanamsa (function):", sky_ay)
    print("Skyfield sidereal (trop - ay):", (tropical_lon - sky_ay) if (tropical_lon is not None and sky_ay is not None) else None)
    print("--- SwissEphem ---")
    print("Swiss trop (calc_ut):", swe_trop)
    print("Swiss sid (calc_ut):", swe_sid)
    print("Swiss ayanamsa (trop - sid):", swe_ay)
    print("Swiss sidereal (calc_ut):", swe_sid)
    print("Market SW ayanamsa (from screenshot): 23.5086°")
