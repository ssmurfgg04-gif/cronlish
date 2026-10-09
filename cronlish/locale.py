"""Compact, deterministic descriptions using the existing cron parser."""
from __future__ import annotations

from typing import Callable

from cronlish.describe import (
    _DAYS, _MACROS, _MONTHS, _SPECS, _Field, _is_star, _parse_field,
    _runs, _step_idiom, describe,
)


def _values(field: _Field, fmt: Callable[[int], str] = str) -> str:
    items = []
    for run in _runs(field.values):
        if run.step == 1 and run.start != run.end:
            items.append(f"{fmt(run.start)}-{fmt(run.end)}")
        else:
            items.extend(fmt(value) for value in
                         range(run.start, run.end + 1, run.step))
    return ",".join(items)


def terse(expr: str) -> str:
    """Describe a supported cron expression compactly, or raise DescribeError.

    Validation, macros, weekday names and field parsing are shared with
    describe(). Lists are sorted and restricted day fields retain cron's OR.
    """
    # Reuse the public validation path, including its actionable error messages.
    describe(expr)
    expanded = _MACROS.get(expr.strip().lower(), expr)
    minute, hour, dom, month, dow = (
        _parse_field(token, spec, expanded)
        for token, spec in zip(expanded.split(), _SPECS)
    )
    clock = len(minute.values) == 1 and len(hour.values) == 1
    if clock:
        time = f"{hour.values[0]:02d}:{minute.values[0]:02d}"
    else:
        step = _step_idiom(minute)
        if _is_star(minute):
            time = "every min"
        elif step is not None:
            time = f"every {step} min"
        else:
            time = "min-" + _values(minute)
        if not _is_star(hour):
            step = _step_idiom(hour)
            time += (f" every {step} hr" if step is not None
                     else " hr-" + _values(hour))

    days = []
    if not _is_star(dom):
        days.append("dom-" + _values(dom))
    if not _is_star(dow):
        days.append(_values(dow, lambda value: _DAYS[value][:3]))
    date = " or ".join(days)
    if not _is_star(month):
        months = "month-" + _values(month, lambda value: _MONTHS[value - 1][:3])
        # The month restriction applies to either day condition.
        if len(days) == 2:
            date = f"({date})"
        date = f"{date} {months}".strip()
    if not date and clock:
        date = "daily"
    return f"{time} {date}".strip()
