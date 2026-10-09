"""Compact, deterministic English output using the standard cron parser."""
from __future__ import annotations

from typing import Callable, Optional

from cronlish.describe import _Field, _is_star, _parse_expression, _runs, _step_idiom

__all__ = ["terse"]

_DAYS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _compact(field: _Field, names: Optional[Callable[[int], str]] = None) -> str:
    """Render normalized values, preserving all restrictions in each field."""
    if names is None:
        if _is_star(field):
            return "*"
        step = _step_idiom(field)
        if step is not None:
            return f"*/{step}"
    fmt = names if names is not None else str
    parts = []
    for run in _runs(field.values):
        if run.start == run.end:
            parts.append(fmt(run.start))
        elif run.step == 1:
            parts.append(f"{fmt(run.start)}-{fmt(run.end)}")
        elif names is not None:
            parts.extend(fmt(v) for v in range(run.start, run.end + 1, run.step))
        else:
            parts.append(f"{run.start}-{run.end}/{run.step}")
    return ",".join(parts)


def _time(minute: _Field, hour: _Field) -> str:
    """Use clock notation for a single time, field notation otherwise."""
    if len(minute.values) == len(hour.values) == 1:
        return f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    if _is_star(minute):
        head = "every min"
    elif _step_idiom(minute) is not None:
        head = f"every {_step_idiom(minute)} min"
    else:
        head = f"min-{_compact(minute)}"
        if _is_star(hour):
            return head + " hourly"
    if not _is_star(hour):
        head += f" h-{_compact(hour)}"
    return head


def terse(expr: str) -> str:
    """Describe a cron expression compactly; raise DescribeError if invalid.

    Numeric restrictions use min-, h-, and dom- prefixes; weekdays and
    months use three-letter names. Restricted day-of-month and day-of-week
    retain classic cron's OR semantics, with months applied to both sides.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    parts = [_time(minute, hour)]
    dom_text = "" if _is_star(dom) else "dom-" + _compact(dom)
    dow_text = "" if _is_star(dow) else _compact(dow, _DAYS.__getitem__)
    if dom_text and dow_text:
        parts.append(f"({dom_text} or {dow_text})")
    elif dom_text or dow_text:
        parts.append(dom_text or dow_text)
    if not _is_star(month):
        parts.append("in-" + _compact(month, lambda v: _MONTHS[v - 1]))
    elif not dom_text and not dow_text and len(minute.values) == len(hour.values) == 1:
        parts.append("daily")
    return " ".join(parts)
