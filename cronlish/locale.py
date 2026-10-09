"""Compact, deterministic cron descriptions for logs and agent pipelines.

:func:`terse` translates a five-field cron expression into one short,
byte-stable string; identical input always yields byte-identical output.
It reuses the field parser from :mod:`cronlish.describe`, so malformed
expressions raise the same :class:`DescribeError` with the same messages.

>>> terse("*/5 * * * *")
'every 5 min'
>>> terse("0 9 * * MON-FRI")
'09:00 Mon-Fri'
"""
from __future__ import annotations

from typing import Callable

from cronlish.describe import (
    DescribeError,
    _is_star,
    _MACROS,
    _parse_field,
    _runs,
    _SPECS,
    _step_idiom,
)

__all__ = ["terse"]

_DOW_ABBR = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")


def _compact(values: tuple, fmt: Callable[[int], str]) -> str:
    """Render sorted values as ``1,15`` / ``1-5`` runs; stepped runs expand."""
    parts = []
    for run in _runs(values):
        if run.start == run.end:
            parts.append(fmt(run.start))
        elif run.step == 1:
            parts.append(f"{fmt(run.start)}-{fmt(run.end)}")
        else:
            parts.append(",".join(fmt(v)
                                  for v in range(run.start, run.end + 1, run.step)))
    return ",".join(parts)


def terse(expr: str) -> str:
    """Translate a five-field cron expression into one terse string.

    Time part: ``every {n} min`` for ``*/n`` steps, ``HH:MM`` for a fixed
    clock time, otherwise a compact ``m:../h:..`` encoding. Date part is
    appended only when day-of-month, month, or day-of-week is restricted
    (`` daily`` when the time is fixed but the date is not).
    """
    raw = expr.strip()
    # Macros are case-insensitive single tokens; expand before five-field parsing.
    key = raw.lower()
    if key in _MACROS:
        expr = _MACROS[key]
    fields = expr.split()
    if any(field.startswith("@") for field in fields):
        raise DescribeError(f"invalid cron expression {raw!r}: unknown macro; "
                            "supported macros are " + ", ".join(sorted(_MACROS)))
    if len(fields) != 5:
        raise DescribeError(f"invalid cron expression {expr!r}: expected 5 space-"
                            "separated fields (minute hour day-of-month month "
                            f"day-of-week), got {len(fields)}")
    minute, hour, dom, month, dow = (
        _parse_field(token, spec, expr) for token, spec in zip(fields, _SPECS))

    step_m = _step_idiom(minute)
    if _is_star(minute) and _is_star(hour):
        time = "every min"
    elif step_m is not None and _is_star(hour):
        time = f"every {step_m} min"
    elif len(minute.values) == 1 and len(hour.values) == 1:
        time = f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    else:
        time = ("m:" + _compact(minute.values, str)
                + " h:" + _compact(hour.values, str))

    star_dom, star_mon, star_dow = _is_star(dom), _is_star(month), _is_star(dow)
    if star_dom and star_mon and star_dow:
        date = "" if time.startswith("every") else " daily"
    else:
        bits = []
        if not star_dom:
            bits.append("dom-" + _compact(dom.values, str))
        if not star_mon:
            bits.append("mon-" + _compact(month.values, str))
        if not star_dow:
            bits.append(_compact(dow.values, _DOW_ABBR.__getitem__))
        date = " " + " ".join(bits)
    return time + date
