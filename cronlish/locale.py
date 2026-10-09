"""Compact deterministic rendering for validated cron expressions."""
from __future__ import annotations

from typing import Callable, List

from cronlish.describe import _Field, _is_star, _parse_expression, _runs, _step_idiom

__all__ = ["terse"]

_DAYS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _compact(field: _Field, label: Callable[[int], str] = str) -> str:
    """Return a stable comma/range representation of parsed field values."""
    parts: List[str] = []
    for run in _runs(field.values):
        if run.start == run.end:
            parts.append(label(run.start))
        elif run.step == 1:
            parts.append(f"{label(run.start)}-{label(run.end)}")
        else:
            parts.extend(label(value)
                         for value in range(run.start, run.end + 1, run.step))
    return ",".join(parts)


def _terse_time(minute: _Field, hour: _Field) -> str:
    """Render the minute/hour pair without losing either restriction."""
    if len(minute.values) == 1 and len(hour.values) == 1:
        return f"{hour.values[0]:02d}:{minute.values[0]:02d}"

    minute_step = _step_idiom(minute)
    if _is_star(minute):
        result = "every min"
    elif minute_step is not None:
        result = f"every {minute_step} min"
    else:
        result = "min-" + _compact(minute)

    if not _is_star(hour):
        result += " hour-" + _compact(hour)
    elif not _is_star(minute) and minute_step is None:
        result += " hourly"
    return result


def terse(expr: str) -> str:
    """Return a compact deterministic description of a cron expression.

    The same parser and :class:`~cronlish.describe.DescribeError` behavior as
    :func:`cronlish.describe.describe` are used. Fixed times use ``HH:MM``;
    calendar restrictions use ``dom-`` and ``mon-`` labels. A vertical bar
    records classic cron's OR relationship when both day fields are restricted.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    parts = [_terse_time(minute, hour)]

    dom_text = "" if _is_star(dom) else "dom-" + _compact(dom)
    dow_text = "" if _is_star(dow) else _compact(dow, _DAYS.__getitem__)
    if dom_text and dow_text:
        parts.append(f"{dom_text}|{dow_text}")
    elif dom_text or dow_text:
        parts.append(dom_text or dow_text)

    if not _is_star(month):
        parts.append("mon-" + _compact(month, lambda value: _MONTHS[value - 1]))
    elif (len(parts) == 1 and len(minute.values) == 1
          and len(hour.values) == 1):
        parts.append("daily")

    return " ".join(parts)
