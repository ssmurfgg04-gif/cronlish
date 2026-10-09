"""Compact locale styles for cronlish output.

``terse`` shrinks a cron expression into a short, deterministic string suited
to logs and agent pipelines. Default ``describe`` output is unchanged when
no locale style is requested.
"""
from __future__ import annotations

from cronlish.describe import (
    DescribeError,
    _DAYS,
    _DOW_NAMES,
    _MACROS,
    _SPECS,
    _is_star,
    _parse_field,
    _runs,
    _step_idiom,
)

__all__ = ["terse", "STYLES"]

STYLES = ("terse",)

_DOW_ABBREV = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")


def terse(expr: str) -> str:
    """Return a compact, deterministic description of a cron expression.

    Examples (exact):
        terse("*/5 * * * *")       -> "every 5 min"
        terse("0 9 * * MON-FRI")   -> "09:00 Mon-Fri"
        terse("30 14 1 * *")       -> "14:30 dom-1"
        terse("0 9 * * *")         -> "09:00 daily"
    """
    raw = expr.strip()
    key = raw.lower()
    if key in _MACROS:
        expr = _MACROS[key]
    fields = expr.split()
    if any(field.startswith("@") for field in fields):
        raise DescribeError(
            f"invalid cron expression {raw!r}: unknown macro; "
            "supported macros are " + ", ".join(sorted(_MACROS))
        )
    if len(fields) != 5:
        raise DescribeError(
            f"invalid cron expression {expr!r}: expected 5 space-"
            "separated fields (minute hour day-of-month month "
            f"day-of-week), got {len(fields)}"
        )
    minute, hour, dom, month, dow = [
        _parse_field(token, spec, expr) for token, spec in zip(fields, _SPECS)
    ]

    step_m = _step_idiom(minute)
    if (
        step_m is not None
        and _is_star(hour)
        and _is_star(dom)
        and _is_star(month)
        and _is_star(dow)
    ):
        return f"every {step_m} min"

    if (
        _is_star(minute)
        and _is_star(hour)
        and _is_star(dom)
        and _is_star(month)
        and _is_star(dow)
    ):
        return "every min"

    clock = None
    if len(minute.values) == 1 and len(hour.values) == 1:
        clock = f"{hour.values[0]:02d}:{minute.values[0]:02d}"

    if clock is not None:
        if _is_star(dom) and _is_star(month) and _is_star(dow):
            return f"{clock} daily"
        if _is_star(dom) and _is_star(month) and not _is_star(dow):
            return f"{clock} {_terse_dow(dow)}"
        if not _is_star(dom) and _is_star(month) and _is_star(dow):
            return f"{clock} {_terse_dom(dom)}"
        # Fallback: clock + whatever suffixes apply
        parts = [clock]
        if not _is_star(dom):
            parts.append(_terse_dom(dom))
        if not _is_star(dow):
            parts.append(_terse_dow(dow))
        if not _is_star(month):
            parts.append(_terse_month(month))
        return " ".join(parts)

    # Non-clock fallbacks kept deterministic and compact
    bits = []
    if not _is_star(minute):
        step = _step_idiom(minute)
        if step is not None:
            bits.append(f"every {step} min")
        elif len(minute.values) == 1:
            bits.append(f"m{minute.values[0]}")
        else:
            bits.append("m" + ",".join(str(v) for v in minute.values))
    if not _is_star(hour):
        step = _step_idiom(hour)
        if step is not None:
            bits.append(f"every {step} h")
        elif len(hour.values) == 1:
            bits.append(f"h{hour.values[0]}")
        else:
            bits.append("h" + ",".join(str(v) for v in hour.values))
    if not _is_star(dom):
        bits.append(_terse_dom(dom))
    if not _is_star(month):
        bits.append(_terse_month(month))
    if not _is_star(dow):
        bits.append(_terse_dow(dow))
    return " ".join(bits) if bits else "every min"


def _terse_dow(dow) -> str:
    runs = _runs(dow.values)
    if len(runs) == 1 and runs[0].step == 1 and runs[0].start != runs[0].end:
        return f"{_DOW_ABBREV[runs[0].start]}-{_DOW_ABBREV[runs[0].end]}"
    if len(dow.values) == 1:
        return _DOW_ABBREV[dow.values[0]]
    return "-".join(_DOW_ABBREV[v] for v in dow.values)  # unlikely; keep deterministic


def _terse_dom(dom) -> str:
    if len(dom.values) == 1:
        return f"dom-{dom.values[0]}"
    return "dom-" + ",".join(str(v) for v in dom.values)


def _terse_month(month) -> str:
    if len(month.values) == 1:
        return f"mon-{month.values[0]}"
    return "mon-" + ",".join(str(v) for v in month.values)
