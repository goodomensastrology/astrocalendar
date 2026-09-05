"""Isolates ALL Swiss Ephemeris calls.
Only this module imports swisseph.
Everything else in the project uses the plain dicts returned here."""

import swisseph as swe
from datetime import datetime, timezone, timedelta

# Planet identifiers (Swiss Ephemeris constants)
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

# Tropical zodiac (or set swe.FLG_SIDEREAL with ayanamsa for sidereal)
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED  # include speed for stations

def _to_jd(dt: datetime) -> float:
    """Convert a UTC datetime to Julian Day."""
    return swe.julday(
        dt.year, dt.month, dt.day,
        dt.hour + dt.minute/60 + dt.second/3600
    )

def planet_position(name: str, dt: datetime) -> dict:
    """Return a planet's ecliptic longitude + speed at a moment (UTC)."""
    body = PLANETS[name]
    jd = _to_jd(dt)
    # pos[0] = longitude, pos[3] = speed (deg/day), pos[1]=lat
    pos, ret = swe.calc_ut(jd, body, FLAGS)
    return {
        "name": name,
        "longitude": pos[0],   # degrees 0-360
        "speed": pos[3],       # deg/day, negative = retrograde
        "retrograde": pos[3] < 0,
        "jd": jd,
    }

def planet_positions(dt: datetime) -> dict:
    """Return all planets at a moment (UTC)."""
    return {name: planet_position(name, dt) for name in PLANETS}

def jd_to_datetime(jd):
    """Convert a Julian Day number to a UTC datetime."""
    y, m, d, h_frac = swe.revjul(jd)
    hour = int(h_frac)
    minute = int((h_frac - hour) * 60)
    second = int(((h_frac - hour) * 60 - minute) * 60)
    return datetime(y, m, d, hour, minute, second, tzinfo=timezone.utc)
