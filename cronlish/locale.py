"""Compact, deterministic cron descriptions for logs and dashboards."""
from __future__ import annotations

from typing import Callable

from cronlish.describe import _Field, _is_star, _parse_expression, _runs, _step_idiom

__all__ = ["terse"]

_DAYS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _compact(field: _Field, fmt: Callable[[int], str] = str) -> str:
    items = []
    for run in _runs(field.values):
        item = fmt(run.start)
        if run.start != run.end:
            item += "-" + fmt(run.end)
            if run.step > 1:
                item += f"/{run.step}"
        items.append(item)
    return ",".join(items)


def _time(minute: _Field, hour: _Field) -> str:
    if len(minute.values) == 1 and len(hour.values) == 1:
        return f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    step = _step_idiom(minute)
    if _is_star(minute):
        head = "every min"
    elif step is not None:
        head = f"every {step} min"
    else:
        head = "min-" + _compact(minute)
    if _is_star(hour):
        return head
    # Explicit fields avoid implying a continuous interval across skipped hours.
    return head + " hour-" + _compact(hour)


def terse(expr: str) -> str:
    """Describe a validated cron expression compactly, raising DescribeError.

    Macros and validation are shared with describe(). Lists are sorted and
    compressed as inclusive ranges, with /n for arithmetic steps. Restricted
    day-of-month and weekday fields are ORed; month restrictions apply to both.
    Names are fixed English abbreviations, independent of the system locale.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    parts = [_time(minute, hour)]
    day = "" if _is_star(dom) else "dom-" + _compact(dom)
    weekday = "" if _is_star(dow) else _compact(dow, _DAYS.__getitem__)
    if day and weekday:
        parts.append(f"({day} or {weekday})")
    elif day or weekday:
        parts.append(day or weekday)
    if not _is_star(month):
        parts.append(_compact(month, lambda value: _MONTHS[value - 1]))
    if len(parts) == 1 and len(minute.values) == len(hour.values) == 1:
        parts.append("daily")
    return " ".join(parts)
