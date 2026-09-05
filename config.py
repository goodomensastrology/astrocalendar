"""User-adjustable settings: orbs, event types, zodiac."""

# Orb (in degrees) per planet pair; falls back to DEFAULT_ORB
ORBS = {
    ("Sun", "Moon"): 8.0,
    ("Mercury", "Venus"): 6.0,
    ("Jupiter", "Saturn"): 5.0,
    ("Uranus", "Neptune"): 3.0,
}
DEFAULT_ORB = 2.0

# Which event types to include
INCLUDE_ECLIPSES = True
INCLUDE_STATIONS = True
INCLUDE_INGRESSES = True
INCLUDE_ASPECTS = True

# Zodiac system
ZODIAC = "tropical"  # or "sidereal"
