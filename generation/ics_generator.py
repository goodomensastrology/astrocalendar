"""Build an .ics file from a list of event dicts."""

from icalendar import Calendar, Event, vDatetime
from datetime import timedelta
from events.detectors import SIGNS, _sign_degree


def build_ics(events, tz="UTC"):
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
    if ev["type"] == "orb":
        return f"{ev['a']} {ev['aspect'].title()} {ev['b']} {ev['subtype']} orb"
    if ev["type"] == "station":
        return f"{ev['planet']} stations {ev['direction']}"
    if ev["type"] == "eclipse":
        return f"{ev['kind']} Eclipse"
    if ev["type"] == "lunation":
        return f"{ev['kind']} Moon in {SIGNS[ev['sign']]}"
    return ev["type"]


def _fmt(dt):
    return dt.strftime("%b %d, %Y %H:%M UTC")


def _description(ev):
    if ev["type"] == "ingress":
        return f"{ev['planet']} crosses 0° {SIGNS[ev['sign']]}"
    if ev["type"] == "aspect":
        desc = f"{ev['a']} {ev['aspect']} {ev['b']} (exact, orb {ev['orb']}°)"
        if ev.get("orb_start") and ev.get("orb_end"):
            desc += (f". Within orb {_fmt(ev['orb_start'])}"
                     f" to {_fmt(ev['orb_end'])}")
        elif ev.get("orb_start"):
            desc += f". Within orb from {_fmt(ev['orb_start'])}"
        return desc
    if ev["type"] == "orb":
        return f"{ev['a']} {ev['aspect']} {ev['b']} {ev['subtype']} {ev['orb']}° orb"
    if ev["type"] == "station":
        return f"{ev['planet']} stations {ev['direction']}"
    if ev["type"] == "eclipse":
        return f"{ev['kind']} Eclipse"
    if ev["type"] == "lunation":
        return f"{ev['kind']} Moon at {_sign_degree(ev['longitude'])}"
    return ev["type"]
