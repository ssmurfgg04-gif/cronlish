"""Compact, deterministic locale-style formatting for cron expressions."""
from __future__ import annotations

from typing import List, Tuple

from cronlish.describe import (
    DescribeError,
    _MACROS,
    _SPECS,
    _is_star,
    _parse_field,
    _runs,
    _step_idiom,
)

__all__ = ["terse"]

_DOW_ABBR = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTH_ABBR = ("jan", "feb", "mar", "apr", "may", "jun",
               "jul", "aug", "sep", "oct", "nov", "dec")


def _parse(expr: str):
    raw = expr.strip()
    key = raw.lower()
    if key in _MACROS:
        expr = _MACROS[key]
    fields = expr.split()
    if any(field.startswith("@") for field in fields):
        raise DescribeError(
            f"invalid cron expression {raw!r}: unknown macro; supported macros are "
            + ", ".join(sorted(_MACROS))
        )
    if len(fields) != 5:
        raise DescribeError(
            f"invalid cron expression {expr!r}: expected 5 space-separated fields "
            f"(minute hour day-of-month month day-of-week), got {len(fields)}"
        )
    return [_parse_field(token, spec, expr) for token, spec in zip(fields, _SPECS)]


def _terse_field(field) -> str:
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


def _terse_time(minute, hour) -> Tuple[str, bool]:
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
    return f"{_terse_field(minute)} {_terse_field(hour)}", False


def _terse_dow(dow) -> str:
    parts: List[str] = []
    for run in _runs(dow.values):
        if run.start == run.end:
            parts.append(_DOW_ABBR[run.start])
        elif run.step == 1:
            parts.append(f"{_DOW_ABBR[run.start]}-{_DOW_ABBR[run.end]}")
        else:
            stepped = ",".join(
                _DOW_ABBR[v] for v in range(run.start, run.end + 1, run.step)
            )
            parts.append(stepped)
    return ",".join(parts)


def _terse_month(month) -> str:
    parts: List[str] = []
    for run in _runs(month.values):
        if run.start == run.end:
            parts.append(_MONTH_ABBR[run.start - 1])
        elif run.step == 1:
            parts.append(f"{_MONTH_ABBR[run.start - 1]}-{_MONTH_ABBR[run.end - 1]}")
        else:
            stepped = ",".join(
                _MONTH_ABBR[v - 1] for v in range(run.start, run.end + 1, run.step)
            )
            parts.append(stepped)
    return ",".join(parts)


def _terse_date(dom, month, dow) -> str | None:
    if _is_star(dom) and _is_star(month) and _is_star(dow):
        return None
    parts: List[str] = []
    if not _is_star(dom):
        parts.append("dom-" + _terse_field(dom))
    if not _is_star(month):
        parts.append("in-" + _terse_month(month))
    if not _is_star(dow):
        parts.append(_terse_dow(dow))
    return " ".join(parts)


def terse(expr: str) -> str:
    """Translate a five-field cron expression into compact terse output.

    Deterministic: identical input always yields byte-identical output.
    Raises :class:`DescribeError` for malformed expressions, exactly like
    :func:`cronlish.describe.describe`.
    """
    minute, hour, dom, month, dow = _parse(expr)
    time, recurring = _terse_time(minute, hour)
    date = _terse_date(dom, month, dow)
    if date:
        return f"{time} {date}"
    if recurring:
        return time
    return f"{time} daily"
