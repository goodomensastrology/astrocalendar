"""Entry point: generate the transit feed .ics file."""

import itertools
from datetime import datetime, timedelta, timezone
from calculation.ephemeris import PLANETS
from events.detectors import (find_ingress, find_aspects, find_stations,
                              find_eclipses, find_lunations)
from generation.ics_generator import build_ics
import config


def generate_feed(start, end, output_path="transits.ics"):
    events = []

    if config.INCLUDE_INGRESSES:
        for planet in PLANETS:
            events += list(find_ingress(planet, start, end))

    if config.INCLUDE_ASPECTS:
        for a, b in itertools.combinations(PLANETS, 2):
            if not config.INCLUDE_MOON_ASPECTS and "Moon" in (a, b):
                continue
            orb = config.ORBS.get((a, b),
                                  config.ORBS.get((b, a), config.DEFAULT_ORB))
            pair_events = list(find_aspects(
                a, b, start, end, orb_deg=orb,
                emit_orb_events=config.EMIT_ORB_EVENTS))
            if not config.INCLUDE_SUN_ASPECTS and "Sun" in (a, b):
                # Sun aspects off by default — keep only conjunctions
                pair_events = [e for e in pair_events
                               if e.get("aspect") == "conjunction"]
            events += pair_events

    if config.INCLUDE_LUNATIONS:
        events += list(find_lunations(start, end))

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
