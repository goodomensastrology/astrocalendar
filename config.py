"""User-adjustable settings: orbs, event types, zodiac."""

# Orb (in degrees) per planet pair; falls back to DEFAULT_ORB.
# Pair order doesn't matter — ("Sun","Moon") and ("Moon","Sun") both work.
ORBS = {
    ("Sun", "Moon"): 8.0,
    ("Mercury", "Venus"): 6.0,
    ("Jupiter", "Saturn"): 5.0,
    ("Uranus", "Neptune"): 3.0,
}
DEFAULT_ORB = 2.0

# --- Event types on/off ---
INCLUDE_INGRESSES = True
INCLUDE_ASPECTS = True
INCLUDE_STATIONS = True
INCLUDE_ECLIPSES = True
INCLUDE_LUNATIONS = True       # New & Full Moons

# Moon aspects are very frequent (the Moon moves ~13°/day), so they are
# OFF by default. Set to True if you want them.
INCLUDE_MOON_ASPECTS = False

# If True, also emits separate "enters orb" / "leaves orb" events.
# Off by default to keep the calendar clean — the orb window is always
# noted in each aspect event's description instead.
EMIT_ORB_EVENTS = False

ZODIAC = "tropical"   # or "sidereal"
