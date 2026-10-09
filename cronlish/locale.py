"""Compact, deterministic ``terse`` rendering of cron expressions.

:func:`terse` turns a five-field cron expression into a short one-liner for
logs, dashboards and agent pipelines, where the full sentence from
:func:`cronlish.describe` is too bulky. Like ``describe``, it is
deterministic: identical input always yields byte-identical output.

Grammar (one example per shape)::

    */5 * * * *       -> every 5 min
    * * * * *         -> every min
    0 9 * * *         -> 09:00 daily
    0 9 * * MON-FRI   -> 09:00 Mon-Fri
    30 14 1 * *       -> 14:30 dom-1
    0 9 1 * MON       -> 09:00 (dom-1 or Mon)   # cron OR semantics
    15,45 10 * * *    -> min-15,45 hour-10
    0 */6 * * *       -> min-0 hour-*/6
"""
from __future__ import annotations

from typing import List, Tuple

from cronlish.describe import _Field, _is_star, _parse_fields, _runs, _step_idiom

__all__ = ["terse"]

_MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
# indexed by cron value; both 0 and 7 mean Sunday
_DOW_ABBR = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")


def _render_numeric(field: _Field) -> str:
    """Render a parsed numeric field compactly: ``*``, ``*/n``, ``a-b`` or lists."""
    if _is_star(field):
        return "*"
    step = _step_idiom(field)
    if step is not None:
        return f"*/{step}"
    runs = _runs(list(field.values))
    if len(runs) == 1 and runs[0].step == 1:
        run = runs[0]
        return str(run.start) if run.start == run.end else f"{run.start}-{run.end}"
    return ",".join(str(v) for v in field.values)


def _render_named(field: _Field, names: "Tuple[str, ...]", base: int = 0) -> str:
    """Render a restricted month or day-of-week field with 3-letter names.

    ``base`` is the cron value of ``names[0]`` (0 for day-of-week, 1 for
    month, whose legal values start at 1).
    """
    values = sorted({0 if v == 7 else v for v in field.values})
    if len(values) == 1:
        return names[values[0] - base]
    if values == list(range(values[0], values[-1] + 1)):
        return f"{names[values[0] - base]}-{names[values[-1] - base]}"
    return ",".join(names[v - base] for v in values)


def _date_suffix(dom: _Field, month: _Field, dow: _Field) -> str:
    """Render the date part for clock-style times; ``daily`` when unrestricted."""
    if _is_star(dom) and _is_star(month) and _is_star(dow):
        return "daily"
    if not _is_star(dom) and not _is_star(dow):
        # cron semantics: restricted dom AND dow match either one
        month_s = f" {_render_named(month, _MONTH_ABBR, base=1)}" if not _is_star(month) else ""
        return f"(dom-{_render_numeric(dom)} or {_render_named(dow, _DOW_ABBR)}){month_s}"
    parts: List[str] = []
    if not _is_star(dom):
        parts.append(f"dom-{_render_numeric(dom)}")
    if not _is_star(month):
        parts.append(_render_named(month, _MONTH_ABBR, base=1))
    if not _is_star(dow):
        parts.append(_render_named(dow, _DOW_ABBR))
    return " ".join(parts)


def terse(expr: str) -> str:
    """Translate a five-field cron expression into one compact terse line.

    Raises :class:`DescribeError` on malformed input, exactly like
    :func:`cronlish.describe`.
    """
    minute, hour, dom, month, dow = _parse_fields(expr)

    if _is_star(minute) and _is_star(hour):
        return "every min"
    step = _step_idiom(minute)
    if step is not None and _is_star(hour):
        return f"every {step} min"
    if len(minute.values) == 1 and len(hour.values) == 1:
        clock = f"{hour.values[0]:02d}:{minute.values[0]:02d}"
        return f"{clock} {_date_suffix(dom, month, dow)}"
    return f"min-{_render_numeric(minute)} hour-{_render_numeric(hour)}"
