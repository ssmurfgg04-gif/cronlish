"""Translate five-field cron expressions into deterministic plain-language English.

:func:`describe` turns a standard crontab line (minute, hour, day-of-month,
month, day-of-week) into one stable English sentence; identical input always
yields byte-identical output. Supported: values, ranges (a-b), lists
(a,b,c) and steps (*/n, a-b/n) in every field; the cron macros
@hourly, @daily/@midnight, @weekly, @monthly and @yearly/@annually;
weekday names MON-SUN (0 and 7 are both Sunday). Anything
else raises :class:`DescribeError` saying what to do instead.

>>> describe("*/5 * * * *")
'Every 5 minutes'
>>> describe("0 9 * * MON-FRI")
'At 09:00, Monday through Friday'
"""
from __future__ import annotations

from typing import Callable, List, NamedTuple, Optional, Sequence, Tuple

__all__ = ["DescribeError", "describe"]

_MACROS = {
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
}


_MONTHS = ("January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December")
_DAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
         "Friday", "Saturday")
_DOW_NAMES = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}

# (name, smallest value, largest value, steps_ok, wraps_top_value)
_FieldSpec = NamedTuple("_FieldSpec", [("name", str), ("lo", int), ("hi", int),
                                       ("steps", bool), ("wrap", bool)])
_SPECS = (
    _FieldSpec("minute", 0, 59, True, False),
    _FieldSpec("hour", 0, 23, True, False),
    _FieldSpec("day-of-month", 1, 31, True, False),
    _FieldSpec("month", 1, 12, True, False),
    _FieldSpec("day-of-week", 0, 7, True, True),
)
# an arithmetic run of values: start, start+step, ..., end (all inclusive)
_Run = NamedTuple("_Run", [("start", int), ("end", int), ("step", int)])
# one parsed field: its spec plus sorted, distinct values
_Field = NamedTuple("_Field", [("spec", _FieldSpec), ("values", Tuple[int, ...])])

class DescribeError(ValueError):
    """Raised when a cron expression is malformed or uses unsupported syntax."""

def _err(expr, spec, detail):
    """Build a DescribeError that names the offending field."""
    return DescribeError(f"invalid cron expression {expr!r}: "
                         f"field {_SPECS.index(spec) + 1} ({spec.name}): {detail}")

def _runs(values):
    """Compress a sorted list of distinct values into maximal arithmetic runs."""
    runs, i, n = [], 0, len(values)
    while i < n:
        if (i + 2 < n and values[i + 1] - values[i] > 1
                and values[i + 1] - values[i] == values[i + 2] - values[i + 1]):
            step, j = values[i + 1] - values[i], i + 1
            while j + 1 < n and values[j + 1] - values[j] == step:
                j += 1
        else:
            step, j = 1, i
            while j + 1 < n and values[j + 1] - values[j] == 1:
                j += 1
        runs.append(_Run(values[i], values[j], step))
        i = j + 1
    return runs

def _is_star(field):
    """True when the field admits every legal value, i.e. it is ``*``."""
    top = field.spec.hi - 1 if field.spec.wrap else field.spec.hi
    return list(field.values) == list(range(field.spec.lo, top + 1))

def _step_idiom(field):
    """Return n when the field is exactly equivalent to ``*/n`` for some n > 1."""
    runs = _runs(field.values)
    if _is_star(field) or len(runs) != 1:
        return None
    run, top = runs[0], (field.spec.hi - 1 if field.spec.wrap else field.spec.hi)
    if run.step > 1 and run.start == field.spec.lo and run.end + run.step > top:
        return run.step
    return None

def _value_of(token, spec, expr):
    """Resolve one numeric or weekday-name token to an int, with helpful errors."""
    if token.isdigit():
        value = int(token)
        if not spec.lo <= value <= spec.hi:
            hint = " (0 and 7 are both Sunday)" if spec.wrap else ""
            raise _err(expr, spec, f"value {value} out of range {spec.lo}-{spec.hi}{hint}")
        return value
    if spec.name == "month" and token.isalpha():
        raise _err(expr, spec, "month names like 'JAN' are not supported yet; "
                               "use numbers 1-12 (planned, see issue #3)")
    if spec.name == "day-of-week" and token.upper() in _DOW_NAMES:
        return _DOW_NAMES[token.upper()]
    if spec.name == "day-of-week":
        expected = "*, a number 0-7, a name like MON-FRI, or a comma-separated list"
    else:
        expected = (f"*, a number {spec.lo}-{spec.hi}, a range like a-b, "
                    "or a comma-separated list")
    raise _err(expr, spec, f"invalid token '{token}': expected {expected}")

def _parse_atom(token, spec, expr):
    """Parse one comma-free token into an inclusive (start, end, step) atom."""
    def pair(text):
        parts = text.split("-")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise _err(expr, spec, f"invalid token '{text}': expected a range like a-b")
        start, end = _value_of(parts[0], spec, expr), _value_of(parts[1], spec, expr)
        if start > end:
            raise _err(expr, spec, f"range start {start} is greater than end {end}")
        return start, end

    if token == "*":
        return spec.lo, spec.hi, 1
    if "/" in token:
        left, _, raw = token.partition("/")
        if not raw.isdigit():
            raise _err(expr, spec, f"step must be an integer, got '{raw}'")
        step = int(raw)
        if step < 1:
            raise _err(expr, spec, f"step must be at least 1, got {step}")
        if left == "*":
            return spec.lo, spec.hi, step
        if "-" not in left:
            raise _err(expr, spec, f"step syntax requires '*/n' or 'a-b/n', got '{token}'")
        start, end = pair(left)
        return start, end, step
    if "-" in token:
        start, end = pair(token)
        return start, end, 1
    value = _value_of(token, spec, expr)
    return value, value, 1

def _parse_field(text, spec, expr):
    """Parse one whole field into sorted, distinct values."""
    found = set()
    for token in text.split(","):
        if token == "":
            raise _err(expr, spec, "empty list item")
        start, end, step = _parse_atom(token, spec, expr)
        if step > 1 and not spec.steps:
            raise _err(expr, spec, f"step values in {spec.name} are not supported")
        found.update(range(start, end + 1, step))
    if spec.wrap:
        found = {v % 7 for v in found}
    return _Field(spec, tuple(sorted(found)))

def _render(runs, fmt):
    """Render runs as one readable list; stepped runs are spelled out in full."""
    items: List[str] = []
    for run in runs:
        if run.step == 1:
            items.append(fmt(run.start) if run.start == run.end
                         else f"{fmt(run.start)} through {fmt(run.end)}")
        else:
            items.extend(fmt(v) for v in range(run.start, run.end + 1, run.step))
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]

def _hour_adverbial(hour):
    """Describe the hour field as a ``past ...`` adverbial."""
    if _is_star(hour):
        return "past every hour"
    step = _step_idiom(hour)
    if step is not None:
        return f"past every {step} hours"
    if len(hour.values) == 1:
        return f"past hour {hour.values[0]}"
    return "past hours " + _render(_runs(hour.values), str)

def _time_sentence(minute, hour):
    """Build the time part of the sentence (minute and hour fields)."""
    star_m, star_h, step_m = _is_star(minute), _is_star(hour), _step_idiom(minute)
    if star_m and star_h:
        return "Every minute"
    if step_m is not None and star_h:
        return f"Every {step_m} minutes"
    if star_m:
        return "Every minute " + _hour_adverbial(hour)
    if step_m is not None:
        return f"Every {step_m} minutes " + _hour_adverbial(hour)
    if len(minute.values) == 1 and len(hour.values) == 1:
        return f"At {hour.values[0]:02d}:{minute.values[0]:02d}"
    head = (f"minute {minute.values[0]}" if len(minute.values) == 1
            else "minutes " + _render(_runs(minute.values), str))
    return "At " + head + " " + _hour_adverbial(hour)

def _date_suffix(dom, month, dow, clock):
    """Build the date part: day-of-month, day-of-week, month, and filler."""
    star_dom, star_dow, star_mon = _is_star(dom), _is_star(dow), _is_star(month)
    suffix = ""
    if not star_dom:
        desc = (f"day {dom.values[0]}" if len(dom.values) == 1
                else "days " + _render(_runs(dom.values), str))
        suffix += f" on {desc} of the month"
    if not star_dow:
        names = _render(_runs(dow.values), _DAYS.__getitem__)
        if not star_dom:
            suffix += " or on " + names  # classic cron ORs dom and dow
        elif not star_mon:
            suffix += " on " + names
        else:
            suffix += ", " + names
    if not star_mon:
        suffix += " in " + _render(_runs(month.values), lambda v: _MONTHS[v - 1])
    if not suffix and clock:
        suffix = " every day"
    return suffix

def _parse_expression(expr: str) -> Tuple[_Field, ...]:
    """Validate and expand an expression for all output styles."""
    raw = expr.strip()
    # Macros are case-insensitive single tokens; expand before five-field parsing.
    key = raw.lower()
    if key in _MACROS:
        expr = _MACROS[key]
    fields = expr.split()
    if any(field.startswith("@") for field in fields):
        raise DescribeError(f"invalid cron expression {raw!r}: unknown macro; "
                            "supported macros are "
                            + ", ".join(sorted(_MACROS)))
    if len(fields) != 5:
        raise DescribeError(f"invalid cron expression {expr!r}: expected 5 space-"
                            "separated fields (minute hour day-of-month month "
                            f"day-of-week), got {len(fields)}")
    return tuple(_parse_field(token, spec, expr)
                 for token, spec in zip(fields, _SPECS))


def describe(expr: str) -> str:
    """Translate a five-field cron expression into one English sentence.

    Extra whitespace is fine; weekday names and @macros are case-insensitive.
    Returns a deterministic, human-readable description of when the job
    runs. Raises :class:`DescribeError` with a field-specific, actionable
    message when the expression is malformed or uses syntax that is not
    supported yet.
    """
    minute, hour, dom, month, dow = _parse_expression(expr)
    return _time_sentence(minute, hour) + _date_suffix(
        dom, month, dow, clock=len(minute.values) == 1 and len(hour.values) == 1)
