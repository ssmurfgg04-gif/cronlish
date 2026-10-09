"""Deterministic compact English descriptions, independent of OS locale."""
from __future__ import annotations

from typing import Callable

from cronlish.describe import _Field, _is_star, _parse_expression, _runs

_DAYS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _compact(field: _Field, fmt: Callable[[int], str] = str) -> str:
    items = []
    for run in _runs(field.values):
        if run.step == 1 and run.start != run.end:
            items.append(f"{fmt(run.start)}-{fmt(run.end)}")
        else:
            items.extend(fmt(v) for v in range(run.start, run.end + 1, run.step))
    return ",".join(items)


def terse(expr: str) -> str:
    """Describe any supported cron expression with compact, stable tokens.

    Calendar restrictions retain the parser's day-of-month/day-of-week OR
    semantics. Irregular minute steps are listed rather than presented as
    constant elapsed intervals across the end of an hour.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    clock = len(minute.values) == len(hour.values) == 1
    if clock:
        time = f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    else:
        if _is_star(minute):
            time = "every min"
        else:
            # Only say 'every N min' when the spacing also holds at :59 -> :00.
            step = minute.values[1] if len(minute.values) > 1 else 60
            if (minute.values[0] == 0 and 60 % step == 0
                    and minute.values == tuple(range(0, 60, step))):
                time = f"every {step} min"
            else:
                time = "min-" + _compact(minute)
        if not _is_star(hour):
            time += " hour-" + _compact(hour, lambda v: f"{v:02d}")
        elif time.startswith("min-"):
            time += " hourly"

    days = []
    if not _is_star(dom):
        days.append("dom-" + _compact(dom))
    if not _is_star(dow):
        days.append(_compact(dow, _DAYS.__getitem__))
    date = " or ".join(days)
    if len(days) == 2:
        date = f"({date})"
    if not _is_star(month):
        date += (" " if date else "") + _compact(month, lambda v: _MONTHS[v - 1])
    if not date and clock:
        date = "daily"
    return time + (" " + date if date else "")
