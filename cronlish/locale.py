"""Compact, deterministic output styles for cron expressions.

:func:`terse` renders the same schedule language as :func:`cronlish.describe`
in a terse, byte-stable form suited to logs, dashboards, and agent
pipelines. Same input always yields byte-identical output.

Grammar (one example per shape)::

    */5 * * * *       -> every 5 min
    * * * * *         -> every min
    0 9 * * *         -> 09:00 daily
    0 9 * * MON-FRI   -> 09:00 Mon-Fri
    30 14 1 * *       -> 14:30 dom-1
    0 9 1 * MON       -> 09:00 (dom-1 or Mon)   # cron OR semantics
    0 * * * *         -> :00 every hour
    15,45 10 * * *    -> min-15,45 hour-10
"""
from __future__ import annotations

from typing import List, Tuple

from cronlish.describe import (
    DescribeError,
    _Field,
    _is_star,
    _parse_fields,
    _runs,
    _step_idiom,
)

__all__ = ["terse"]

_DOW_ABBR = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")  # index 0-6
_MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")  # index 0-11


def _terse_field(field: _Field) -> str:
    """Render one parsed numeric field compactly: ``*``, ``*/n`` or runs."""
    if _is_star(field):
        return "*"
    step = _step_idiom(field)
    if step is not None:
        return f"*/{step}"
    parts: List[str] = []
    for run in _runs(field.values):
        if run.start == run.end:
            parts.append(str(run.start))
        elif run.step == 1:
            parts.append(f"{run.start}-{run.end}")
        else:
            parts.append(f"{run.start}-{run.end}/{run.step}")
    return ",".join(parts)


def _terse_time(minute: _Field, hour: _Field) -> "Tuple[str, bool]":
    """Render the time part; the bool flags a recurring (every-…) pattern."""
    star_m, star_h = _is_star(minute), _is_star(hour)
    step_m = _step_idiom(minute)
    if star_m and star_h:
        return "every min", True
    if step_m is not None and star_h:
        return f"every {step_m} min", True
    if len(minute.values) == 1 and star_h:
        return f":{minute.values[0]:02d} every hour", True
    if star_m and len(hour.values) == 1:
        return f"every min @ {hour.values[0]:02d}", True
    if step_m is not None and len(hour.values) == 1:
        return f"every {step_m} min @ {hour.values[0]:02d}", True
    if len(minute.values) == 1 and len(hour.values) == 1:
        return f"{hour.values[0]:02d}:{minute.values[0]:02d}", False
    return f"min-{_terse_field(minute)} hour-{_terse_field(hour)}", False


def _render_named(field: _Field, names: Tuple[str, ...], base: int = 0) -> str:
    """Render a restricted month or day-of-week field with 3-letter names.

    ``base`` is the cron value of ``names[0]`` (0 for day-of-week, 1 for
    month, whose legal values start at 1).
    """
    values = sorted(field.values)
    if len(values) == 1:
        return names[values[0] - base]
    if values == list(range(values[0], values[-1] + 1)):
        return f"{names[values[0] - base]}-{names[values[-1] - base]}"
    return ",".join(names[v - base] for v in values)


def _terse_date(dom: _Field, month: _Field, dow: _Field) -> "str | None":
    """Render the date part, or None when every date field is ``*``."""
    star_dom, star_mon, star_dow = _is_star(dom), _is_star(month), _is_star(dow)
    if star_dom and star_mon and star_dow:
        return None
    if not star_dom and not star_dow:
        # Classic cron fires when EITHER restricted field matches; say so,
        # mirroring describe()'s documented quirk.
        month_s = f" {_render_named(month, _MONTH_ABBR, base=1)}" if not star_mon else ""
        return f"(dom-{_terse_field(dom)} or {_render_named(dow, _DOW_ABBR)}){month_s}"
    parts: List[str] = []
    if not star_dom:
        parts.append("dom-" + _terse_field(dom))
    if not star_mon:
        parts.append("in-" + _render_named(month, _MONTH_ABBR, base=1))
    if not star_dow:
        parts.append(_render_named(dow, _DOW_ABBR))
    return " ".join(parts)


def terse(expr: str) -> str:
    """Translate a five-field cron expression into compact terse output.

    Deterministic: identical input always yields byte-identical output.
    Raises :class:`DescribeError` for malformed expressions, exactly like
    :func:`cronlish.describe.describe`.
    """
    minute, hour, dom, month, dow = _parse_fields(expr)
    time, recurring = _terse_time(minute, hour)
    date = _terse_date(dom, month, dow)
    if date:
        return f"{time} {date}"
    if recurring:
        return time
    return f"{time} daily"
