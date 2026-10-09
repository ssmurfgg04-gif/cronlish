"""Compact cron descriptions using the same validation as ``describe``."""
from __future__ import annotations

from cronlish.describe import (
    _DAYS, _MONTHS, _is_star, _parse_expression, _runs, _step_idiom,
)


def _compact(field, names=None):
    """Render canonical values as comma-separated values/ranges/steps."""
    fmt = str if names is None else names.__getitem__
    items = []
    for run in _runs(field.values):
        if run.start == run.end:
            items.append(fmt(run.start))
        elif run.step == 1:
            items.append(f"{fmt(run.start)}-{fmt(run.end)}")
        elif names is None:
            items.append(f"{run.start}-{run.end}/{run.step}")
        else:
            items.extend(fmt(v) for v in range(run.start, run.end + 1, run.step))
    return ",".join(items)


def terse(expr: str) -> str:
    """Describe any supported cron expression in compact, deterministic form.

    Fixed times use HH:MM; other times name their minute/hour constraints.
    Day constraints use dom-N and abbreviated weekdays, explicitly ORed
    when both are restricted. A trailing month constraint applies to both.
    Malformed expressions raise the same DescribeError as ``describe``.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    clock = len(minute.values) == len(hour.values) == 1
    if clock:
        time = f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    else:
        step = _step_idiom(minute)
        if _is_star(minute):
            time = "every min"
        elif step is not None:
            time = f"every {step} min"
        else:
            time = "min-" + _compact(minute)
        if _is_star(hour):
            if not _is_star(minute) and step is None:
                time += " hourly"
        else:
            time += " hour-" + _compact(hour)

    days = []
    if not _is_star(dom):
        days.append("dom-" + _compact(dom))
    if not _is_star(dow):
        days.append(_compact(dow, tuple(day[:3] for day in _DAYS)))
    if len(days) == 2:
        time += " (" + " or ".join(days) + ")"
    elif days:
        time += " " + days[0]
    elif clock and _is_star(month):
        time += " daily"
    if not _is_star(month):
        time += " in " + _compact(month, ("",) + tuple(m[:3] for m in _MONTHS))
    return time
