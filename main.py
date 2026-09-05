"""Entry point: generate the transit feed .ics file."""

import itertools
from datetime import datetime, timedelta, timezone
from calculation.ephemeris import PLANETS
from events.detectors import find_ingress, find_aspects, find_stations, find_eclipses
from generation.ics_generator import build_ics
import config

def generate_feed(start, end, output_path="transits.ics"):
    events = []

    if config.INCLUDE_INGRESSES:
        for planet in PLANETS:
            events += list(find_ingress(planet, start, end))

    if config.INCLUDE_ASPECTS:
        for a, b in itertools.combinations(PLANETS, 2):
            orb = config.ORBS.get((a, b), config.DEFAULT_ORB)
            events += list(find_aspects(a, b, start, end, orb_deg=orb))

    if config.INCLUDE_STATIONS:
        events += list(find_stations(start, end))

    if config.INCLUDE_ECLIPSES:
        events += list(find_eclipses(start, end))

    events.sort(key=lambda e: e["at"])
    ics = build_ics(events)
    with open(output_path, "w") as f:
        f.write(ics)
    print(f"Wrote {len(events)} events to {output_path}")

if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    generate_feed(now, now + timedelta(days=365))
