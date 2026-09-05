"""Event detection logic: ingresses, aspects, eclipses, stations.
Only imports from calculation.ephemeris — never swisseph directly."""

from calculation.ephemeris import planet_position, PLANETS
from datetime import datetime, timedelta, timezone

# Aspect exact angular separation
ASPECT_DEG = {
    "conjunction": 0,
    "opposition": 180,
    "square": 90,
    "trine": 120,
    "sextile": 60,
}

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def _angular_diff(a: float, b: float) -> float:
    """Smallest angular separation between two longitudes (0-180)."""
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)

def _refine(planet, t1, t2, target):
    """Binary-search refine a crossing time between t1 and t2."""
    for _ in range(40):
        mid = t1 + (t2 - t1) / 2
        val = planet_position(planet, mid)["longitude"]
        if (val - target) > 0:
            t1 = mid
        else:
            t2 = mid
    return t1 + (t2 - t1) / 2

def find_ingress(planet, start, end, step_hours=1):
    """Yield sign ingresses for a planet between start and end."""
    t = start
    prev_sign = int(planet_position(planet, t)["longitude"] // 30)
    while t < end:
        t += timedelta(hours=step_hours)
        lon = planet_position(planet, t)["longitude"]
        sign = int(lon // 30)
        if sign != prev_sign:
            # refine to the exact 0° crossing
            t0 = t - timedelta(hours=step_hours)
            exact = _refine(planet, t0, t, sign * 30.0)
            yield {"type": "ingress", "planet": planet,
                   "sign": sign, "at": exact}
            prev_sign = sign

def find_aspects(planet_a, planet_b, start, end, orb_deg=2.0, step_hours=1):
    """Yield exact aspects when angular separation crosses the aspect degree."""
    t = start
    prev = None
    while t < end:
        t += timedelta(hours=step_hours)
        diff = _angular_diff(
            planet_position(planet_a, t)["longitude"],
            planet_position(planet_b, t)["longitude"]
        )
        for name, deg in ASPECT_DEG.items():
            # did we cross the exact aspect degree?
            if prev is not None and (prev - deg) * (diff - deg) <= 0:
                t0 = t - timedelta(hours=step_hours)
                exact = _refine_aspect(planet_a, planet_b, t0, t, deg)
                yield {"type": "aspect", "a": planet_a, "b": planet_b,
                       "aspect": name, "at": exact}
        prev = diff

def _refine_aspect(pa, pb, t1, t2, target):
    for _ in range(40):
        mid = t1 + (t2 - t1) / 2
        d = _angular_diff(planet_position(pa, mid)["longitude"],
                         planet_position(pb, mid)["longitude"])
        if d > target:
            t1 = mid
        else:
            t2 = mid
    return t1 + (t2 - t1) / 2

def find_stations(start, end, step_hours=1):
    """Yield station events when a planet's speed crosses zero."""
    t = start
    prev = {p: planet_position(p, t)["speed"] for p in PLANETS}
    while t < end:
        t += timedelta(hours=step_hours)
        for p in PLANETS:
            speed = planet_position(p, t)["speed"]
            if prev[p] != 0 and (prev[p] > 0) != (speed > 0):
                t0 = t - timedelta(hours=step_hours)
                exact = _refine_station(p, t0, t)
                direction = "direct" if speed > 0 else "retrograde"
                yield {"type": "station", "planet": p,
                       "direction": direction, "at": exact}
            prev[p] = speed

def _refine_station(planet, t1, t2):
    for _ in range(40):
        mid = t1 + (t2 - t1) / 2
        if planet_position(planet, mid)["speed"] > 0:
            t1 = mid
        else:
            t2 = mid
    return t1 + (t2 - t1) / 2

def find_eclipses(start, end):
    """Use Swiss Ephemeris's dedicated eclipse functions to find real eclipses."""
    import swisseph as swe
    from calculation.ephemeris import _to_jd, jd_to_datetime

    events = []
    # Lunar eclipses
    t = start
    jd_end = _to_jd(end)
    while t < end:
        jd = _to_jd(t)
        res = swe.lun_eclipse_when(jd, swe.FLG_MOSEPH)
        ecl_jd = res[1][0]   # greatest eclipse time
        if ecl_jd > jd_end:
            break
        ecl_dt = jd_to_datetime(ecl_jd)
        events.append({"type": "eclipse", "kind": "Lunar", "at": ecl_dt})
        t = ecl_dt + timedelta(days=15)

    # Solar eclipses
    t = start
    while t < end:
        jd = _to_jd(t)
        res = swe.sol_eclipse_when_glob(jd, swe.FLG_MOSEPH)
        ecl_jd = res[1][0]   # greatest eclipse time
        if ecl_jd > jd_end:
            break
        ecl_dt = jd_to_datetime(ecl_jd)
        events.append({"type": "eclipse", "kind": "Solar", "at": ecl_dt})
        t = ecl_dt + timedelta(days=15)

    return events
