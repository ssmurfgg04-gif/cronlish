"""Tests for cronlish.locale.terse and the --locale-style CLI flag."""
import subprocess
import sys

import pytest

from cronlish import DescribeError
from cronlish.locale import terse


# --- the four acceptance examples from issue #4 -----------------------------

def test_terse_every_five_minutes():
    assert terse("*/5 * * * *") == "every 5 min"


def test_terse_weekday_mornings():
    assert terse("0 9 * * MON-FRI") == "09:00 Mon-Fri"


def test_terse_monthly_afternoon():
    assert terse("30 14 1 * *") == "14:30 dom-1"


def test_terse_daily_clock():
    assert terse("0 9 * * *") == "09:00 daily"


# --- time shapes --------------------------------------------------------------

def test_terse_every_minute():
    assert terse("* * * * *") == "every min"


def test_terse_macros():
    assert terse("@daily") == "00:00 daily"
    assert terse("@hourly") == ":00 every hour"
    assert terse("@weekly") == "00:00 Sun"


def test_terse_single_dow():
    assert terse("0 12 * * SUN") == "12:00 Sun"


def test_terse_dow_list():
    assert terse("0 12 * * MON,WED,FRI") == "12:00 Mon,Wed,Fri"


def test_terse_dow_numeric_range():
    assert terse("0 12 * * 1-5") == "12:00 Mon-Fri"


def test_terse_dom_list():
    assert terse("0 0 1,15 * *") == "00:00 dom-1,15"


def test_terse_month_name():
    assert terse("0 0 1 1 *") == "00:00 dom-1 in-jan"


def test_terse_month_range():
    assert terse("0 0 * 1-3 *") == "00:00 in-jan-mar"
    assert terse("0 0 1 1-3 *") == "00:00 dom-1 in-jan-mar"


# --- determinism --------------------------------------------------------------

def test_terse_deterministic():
    exprs = ["*/5 * * * *", "0 9 * * MON-FRI", "30 14 1 * *",
             "0 9 * * *", "15 10 1 1 MON", "@weekly"]
    for expr in exprs:
        assert terse(expr) == terse(expr)


def test_terse_whitespace_insensitive():
    assert terse("  0 9 * * *  ") == terse("0 9 * * *")


# --- errors match describe() ---------------------------------------------------

def test_terse_bad_expression_raises():
    with pytest.raises(DescribeError):
        terse("banana")


def test_terse_bad_macro_raises():
    with pytest.raises(DescribeError):
        terse("@fortnightly")


# --- CLI flag ------------------------------------------------------------------

def _run_cli(*argv):
    return subprocess.run(
        [sys.executable, "-m", "cronlish.cli", *argv],
        capture_output=True, text=True,
    )


def test_cli_terse_flag():
    proc = _run_cli("--locale-style", "terse", "*/5 * * * *")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "every 5 min"


def test_cli_terse_all_examples():
    cases = {
        "*/5 * * * *": "every 5 min",
        "0 9 * * MON-FRI": "09:00 Mon-Fri",
        "30 14 1 * *": "14:30 dom-1",
        "0 9 * * *": "09:00 daily",
    }
    for expr, expected in cases.items():
        proc = _run_cli("--locale-style", "terse", expr)
        assert proc.returncode == 0, expr
        assert proc.stdout.strip() == expected, expr


def test_cli_unknown_style_exits_2():
    proc = _run_cli("--locale-style", "klingon", "*/5 * * * *")
    assert proc.returncode == 2
    assert "invalid choice" in proc.stderr
    assert "klingon" in proc.stderr


def test_cli_default_output_unchanged():
    proc = _run_cli("*/5 * * * *")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "Every 5 minutes"


def test_cli_terse_bad_expression_exits_2():
    proc = _run_cli("--locale-style", "terse", "banana")
    assert proc.returncode == 2
    assert proc.stderr.startswith("error:")
