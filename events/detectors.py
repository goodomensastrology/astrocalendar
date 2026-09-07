"""Event detection: ingresses, aspects (with orb windows), new/full moons,
stations, and eclipses."""

from datetime import datetime, timedelta, timezone
from calculation.ephemeris import planet_position, PLANETS

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# aspect name -> target separations on the 0-360 circle
ASPECT_TARGETS = {
    "conjunction": [0],
    "sextile": [60, 300],
    "square": [90, 270],
    "trine": [120, 240],
    "opposition": [180],
}


def _sep360(lon_a, lon_b):
    """Separation (lon_a - lon_b) on the circle, in [0, 360)."""
    return (lon_a - lon_b) % 360


def _signed_circ_dist(x, target):
    """Signed circular distance from target to x, in (-180, 180]."""
    return ((x - target + 180) % 360) - 180


def _circ_dist(x, target):
    """Absolute circular distance between x and target, in [0, 180]."""
    d = abs(x - target) % 360
    return min(d, 360 - d)


def _refine_crossing(f, t1, t2, iterations=50):
    """Bisect to find where f(t) crosses zero between t1 and t2."""
    f1 = f(t1)
    for _ in range(iterations):
        mid = t1 + (t2 - t1) / 2
        fm = f(mid)
        if f1 * fm <= 0:
            t2 = mid
        else:
            t1 = mid
            f1 = fm
    return t1 + (t2 - t1) / 2


def _sign_degree(longitude):
    sign = SIGNS[int(longitude // 30) % 12]
    deg = longitude % 30
    return f"{int(deg)}°{int((deg % 1) * 60):02d}' {sign}"


def find_ingress(planet, start, end, step_hours=1):
    t = start
    prev_sign = int(planet_position(planet, t)["longitude"] // 30) % 12
    while t < end:
        t += timedelta(hours=step_hours)
        lon = planet_position(planet, t)["longitude"]
        sign = int(lon // 30) % 12
        if sign != prev_sign:
            target = (sign * 30.0) % 360
            t0 = t - timedelta(hours=step_hours)
            exact = _refine_crossing(
                lambda tt: _signed_circ_dist(
                    planet_position(planet, tt)["longitude"], target),
                t0, t)
            yield {"type": "ingress", "planet": planet, "sign": sign, "at": exact}
            prev_sign = sign


def find_aspects(planet_a, planet_b, start, end, orb_deg=2.0,
                 step_hours=1, emit_orb_events=False):
    crossings = []          # {aspect, kind: enter/exact/leave, at}
    prev_dist = {}          # aspect name -> previous distance to nearest target
    prev_exact = {}         # (name, target) -> previous signed distance

    t = start
    while t < end:
        t += timedelta(hours=step_hours)
        d2 = _sep360(planet_position(planet_a, t)["longitude"],
                     planet_position(planet_b, t)["longitude"])

        for name, targets in ASPECT_TARGETS.items():
            # --- orb boundary crossings (enter / leave) ---
            dist = min(_circ_dist(d2, tg) for tg in targets)
            pdist = prev_dist.get(name)
            if pdist is not None:
                if pdist > orb_deg and dist <= orb_deg:
                    crossings.append({"aspect": name, "kind": "enter", "at": t})
                elif pdist <= orb_deg and dist > orb_deg:
                    crossings.append({"aspect": name, "kind": "leave", "at": t})
            prev_dist[name] = dist

            # --- exact crossings ---
            for tg in targets:
                cur = _signed_circ_dist(d2, tg)
                pcur = prev_exact.get((name, tg))
                if pcur is not None and pcur != 0 and (pcur > 0) != (cur > 0):
                    t0 = t - timedelta(hours=step_hours)
                    exact = _refine_crossing(
                        lambda tt: _signed_circ_dist(
                            _sep360(planet_position(planet_a, tt)["longitude"],
                                    planet_position(planet_b, tt)["longitude"]),
                            tg),
                        t0, t)
                    crossings.append({"aspect": name, "kind": "exact", "at": exact})
                prev_exact[(name, tg)] = cur

    # --- assemble final events ---
    events = []
    for i, c in enumerate(crossings):
        if c["kind"] != "exact":
            continue
        enter = next((x for x in reversed(crossings[:i])
                      if x["aspect"] == c["aspect"] and x["kind"] == "enter"), None)
        leave = next((x for x in crossings[i + 1:]
                      if x["aspect"] == c["aspect"] and x["kind"] == "leave"), None)
        events.append({
            "type": "aspect", "a": planet_a, "b": planet_b,
            "aspect": c["aspect"], "at": c["at"], "orb": orb_deg,
            "orb_start": enter["at"] if enter else None,
            "orb_end": leave["at"] if leave else None,
        })
        if emit_orb_events:
            if enter:
                events.append({"type": "orb", "subtype": "enters",
                               "a": planet_a, "b": planet_b,
                               "aspect": c["aspect"], "at": enter["at"],
                               "orb": orb_deg})
            if leave:
                events.append({"type": "orb", "subtype": "leaves",
                               "a": planet_a, "b": planet_b,
                               "aspect": c["aspect"], "at": leave["at"],
                               "orb": orb_deg})
    return events


def find_lunations(start, end, step_hours=1):
    """New Moons (Sun-Moon conjunction) and Full Moons (opposition)."""
    t = start
    prev_d2 = None
    while t < end:
        t += timedelta(hours=step_hours)
        d2 = _sep360(planet_position("Sun", t)["longitude"],
                     planet_position("Moon", t)["longitude"])
        if prev_d2 is not None:
            for target, kind in ((0, "New"), (180, "Full")):
                cur = _signed_circ_dist(d2, target)
                pcur = _signed_circ_dist(prev_d2, target)
                if pcur != 0 and (pcur > 0) != (cur > 0):
                    t0 = t - timedelta(hours=step_hours)
                    exact = _refine_crossing(
                        lambda tt: _signed_circ_dist(
                            _sep360(planet_position("Sun", tt)["longitude"],
                                    planet_position("Moon", tt)["longitude"]),
                            target),
                        t0, t)
                    lon = planet_position("Sun", exact)["longitude"]
                    yield {"type": "lunation", "kind": kind, "at": exact,
                           "sign": int(lon // 30) % 12, "longitude": lon}
        prev_d2 = d2


def find_stations(start, end, step_hours=1):
    planets = [p for p in PLANETS if p not in ("Sun", "Moon")]
    t = start
    prev = {p: planet_position(p, t)["speed"] for p in planets}
    while t < end:
        t += timedelta(hours=step_hours)
        for p in planets:
            speed = planet_position(p, t)["speed"]
            if prev[p] != 0 and (prev[p] > 0) != (speed > 0):
                t0 = t - timedelta(hours=step_hours)
                exact = _refine_crossing(
                    lambda tt: planet_position(p, tt)["speed"], t0, t)
                direction = "direct" if speed > 0 else "retrograde"
                yield {"type": "station", "planet": p,
                       "direction": direction, "at": exact}
            prev[p] = speed


def find_eclipses(start, end):
    """Real eclipses via Swiss Ephemeris's dedicated functions."""
    import swisseph as swe
    from calculation.ephemeris import _to_jd, jd_to_datetime

    events = []
    jd_end = _to_jd(end)

    t = start
    while t < end:
        jd = _to_jd(t)
        res = swe.lun_eclipse_when(jd, swe.FLG_MOSEPH)
        ecl_jd = res[1][0]
        if ecl_jd > jd_end:
            break
        ecl_dt = jd_to_datetime(ecl_jd)
        events.append({"type": "eclipse", "kind": "Lunar", "at": ecl_dt})
        t = ecl_dt + timedelta(days=15)

    t = start
    while t < end:
        jd = _to_jd(t)
        res = swe.sol_eclipse_when_glob(jd, swe.FLG_MOSEPH)
        ecl_jd = res[1][0]
        if ecl_jd > jd_end:
            break
        ecl_dt = jd_to_datetime(ecl_jd)
        events.append({"type": "eclipse", "kind": "Solar", "at": ecl_dt})
        t = ecl_dt + timedelta(days=15)

    return events
