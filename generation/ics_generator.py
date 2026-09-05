"""Build an .ics file from a list of event dicts."""

from icalendar import Calendar, Event, vDatetime
from datetime import timedelta
from events.detectors import SIGNS

def build_ics(events, tz="UTC") -> str:
    """Convert detected events into an .ics string."""
    cal = Calendar()
    cal.add("prodid", "-//AstroCal//Transit Feed//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "AstroCal Transits")

    for i, ev in enumerate(events):
        event = Event()
        event.add("uid", f"{int(ev['at'].timestamp())}-{i}@astrocal")
        event.add("dtstart", vDatetime(ev["at"]))
        event.add("dtend", vDatetime(ev["at"] + timedelta(hours=1)))
        event.add("summary", _summary(ev))
        event.add("description", _description(ev))
        event.add("categories", ev["type"])
        cal.add_component(event)

    return cal.to_ical().decode("utf-8")

def _summary(ev):
    if ev["type"] == "ingress":
        return f"{ev['planet']} enters {SIGNS[ev['sign']]}"
    if ev["type"] == "aspect":
        return f"{ev['a']} {ev['aspect'].title()} {ev['b']}"
    if ev["type"] == "station":
        return f"{ev['planet']} stations {ev['direction']}"
    if ev["type"] == "eclipse":
        return f"{ev['kind']} Eclipse"
    return ev["type"]

def _description(ev):
    if ev["type"] == "ingress":
        return f"{ev['planet']} crosses 0° {SIGNS[ev['sign']]}"
    if ev["type"] == "aspect":
        return f"{ev['a']} {ev['aspect']} {ev['b']} (exact)"
    if ev["type"] == "station":
        return f"{ev['planet']} stations {ev['direction']}"
    if ev["type"] == "eclipse":
        return f"{ev['kind']} Eclipse"
    return ev["type"]
