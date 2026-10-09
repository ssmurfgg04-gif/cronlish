"""Compact, deterministic descriptions using the shared cron parser."""
from __future__ import annotations

from typing import Callable

from cronlish.describe import (
    _DAYS, _MONTHS, _Field, _is_star, _parse_expression, _runs, _step_idiom,
)

__all__ = ["terse"]


def _values(field: _Field, fmt: Callable[[int], str] = str) -> str:
    """Use hyphens for contiguous ranges and commas for separate values."""
    if _is_star(field):
        return "*"
    items = []
    for run in _runs(field.values):
        if run.step == 1:
            items.append(fmt(run.start) if run.start == run.end
                         else f"{fmt(run.start)}-{fmt(run.end)}")
        else:
            items.extend(fmt(v) for v in range(run.start, run.end + 1, run.step))
    return ",".join(items)


def _time(minute: _Field, hour: _Field) -> str:
    if len(minute.values) == len(hour.values) == 1:
        return f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    if _is_star(hour):
        if _is_star(minute):
            return "every min"
        step = _step_idiom(minute)
        # A step that does not divide 60 has a shorter gap at the next hour.
        if step is not None and 60 % step == 0:
            return f"every {step} min"
        return f"min-{_values(minute)} hourly"
    return f"min-{_values(minute)} hour-{_values(hour)}"


def terse(expr: str) -> str:
    """Describe any supported expression compactly, or raise DescribeError.

    Clock times use HH:MM; other times use minute/hour field labels. Dates
    use dom-N and three-letter weekday/month names. Restricted day-of-month
    and day-of-week fields retain the default formatter's OR semantics.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    parts = [_time(minute, hour)]
    days = []
    if not _is_star(dom):
        days.append(f"dom-{_values(dom)}")
    if not _is_star(dow):
        days.append(_values(dow, lambda v: _DAYS[v][:3]))
    if len(days) == 2:
        parts.append(f"({days[0]} or {days[1]})")
    elif days:
        parts.append(days[0])
    elif len(minute.values) == len(hour.values) == 1:
        parts.append("daily")
    if not _is_star(month):
        parts.append(_values(month, lambda v: _MONTHS[v - 1][:3]))
    return " ".join(parts)
