"""Compact, deterministic descriptions of the same validated cron syntax."""
from __future__ import annotations

from typing import Callable

from cronlish.describe import (
    _Field, _is_star, _parse_expression, _runs, _step_idiom,
)

__all__ = ["terse"]

_DAYS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _values(field: _Field, fmt: Callable[[int], str] = str) -> str:
    """Compact adjacent values without implying a different schedule."""
    parts = []
    for run in _runs(field.values):
        if run.start == run.end:
            parts.append(fmt(run.start))
        elif run.step == 1:
            parts.append(f"{fmt(run.start)}-{fmt(run.end)}")
        else:
            # Spell out stepped named fields too: Mon-Wed-Fri is not a range.
            parts.extend(fmt(v) for v in range(run.start, run.end + 1, run.step))
    return ",".join(parts)


def _time(minute: _Field, hour: _Field) -> str:
    if len(minute.values) == len(hour.values) == 1:
        return f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    step = _step_idiom(minute)
    if _is_star(minute):
        clock = "every min"
    elif step is not None:
        clock = f"every {step} min"
    else:
        clock = "min-" + _values(minute)
    if not _is_star(hour):
        clock += " hour-" + _values(hour)
    elif not _is_star(minute) and step is None:
        clock += " hourly"
    return clock


def terse(expr: str) -> str:
    """Describe a cron expression compactly, raising DescribeError if invalid.

    Fixed times use HH:MM. Other time fields use ``min-``/``hour-`` labels;
    ``dom-`` and ``month-`` qualify calendar fields. Named weekdays and
    months use English abbreviations, independent of the system locale.
    Restricted day-of-month and day-of-week fields are explicitly ORed,
    with parentheses when a month restriction also applies.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    parts = [_time(minute, hour)]
    dom_text = "" if _is_star(dom) else "dom-" + _values(dom)
    dow_text = "" if _is_star(dow) else _values(dow, _DAYS.__getitem__)
    if dom_text and dow_text:
        days = f"{dom_text} or {dow_text}"
        parts.append(days if _is_star(month) else f"({days})")
    elif dom_text or dow_text:
        parts.append(dom_text or dow_text)
    if not _is_star(month):
        parts.append("month-" + _values(month, lambda v: _MONTHS[v - 1]))
    elif len(parts) == 1 and len(minute.values) == len(hour.values) == 1:
        parts.append("daily")
    return " ".join(parts)
