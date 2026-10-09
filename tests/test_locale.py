"""Tests for cronlish.locale.terse and the --locale-style CLI flag."""
import pytest

from cronlish import DescribeError
from cronlish.cli import main
from cronlish.locale import terse


# --- the four acceptance examples from issue #4 (byte-exact) -----------------

def test_terse_every_five_minutes():
    assert terse("*/5 * * * *") == "every 5 min"


def test_terse_weekday_mornings():
    assert terse("0 9 * * MON-FRI") == "09:00 Mon-Fri"


def test_terse_monthly_afternoon():
    assert terse("30 14 1 * *") == "14:30 dom-1"


def test_terse_daily_clock():
    assert terse("0 9 * * *") == "09:00 daily"


# --- every/step shapes --------------------------------------------------------

def test_terse_every_minute_star():
    assert terse("* * * * *") == "every min"


def test_terse_every_minute_step_one():
    assert terse("*/1 * * * *") == "every min"


@pytest.mark.parametrize("expr, expected", [
    ("*/15 * * * *", "every 15 min"),
    ("*/20 * * * *", "every 20 min"),
    ("5-55/10 * * * *", "min-5,15,25,35,45,55 hour-*"),
])
def test_terse_minute_steps(expr, expected):
    assert terse(expr) == expected


# --- clock shapes with date restrictions -------------------------------------

def test_terse_clock_with_dom_list():
    assert terse("0 0 1,15 * *") == "00:00 dom-1,15"


def test_terse_clock_with_dom_range():
    assert terse("0 0 1-5 * *") == "00:00 dom-1-5"


def test_terse_clock_with_dow_list():
    assert terse("0 9 * * MON,WED") == "09:00 Mon,Wed"


def test_terse_clock_with_sunday_zero_and_seven():
    assert terse("0 0 * * 0") == "00:00 Sun"
    assert terse("0 0 * * 7") == "00:00 Sun"


def test_terse_clock_with_month_list():
    assert terse("0 0 1 1,6 *") == "00:00 dom-1 Jan,Jun"


def test_terse_clock_with_month_range():
    assert terse("0 0 * 1-3 *") == "00:00 Jan-Mar"


def test_terse_dom_or_dow_uses_parenthesised_or():
    # cron semantics: restricted dom AND dow match either one
    assert terse("0 9 1 * MON") == "09:00 (dom-1 or Mon)"


def test_terse_dom_or_dow_with_month():
    assert terse("0 9 1 6 MON") == "09:00 (dom-1 or Mon) Jun"


# --- field forms (multi-value minute/hour) -----------------------------------

def test_terse_field_form_listed_minutes():
    assert terse("15,45 10 * * *") == "min-15,45 hour-10"


def test_terse_field_form_hour_step():
    assert terse("0 */6 * * *") == "min-0 hour-*/6"


# --- macros ------------------------------------------------------------------

def test_terse_macro_raises():
    # macros reverted upstream (v0.1); terse must reject them like describe
    with pytest.raises(DescribeError):
        terse("@daily")


# --- errors and determinism ---------------------------------------------------

def test_terse_bad_expression_raises():
    with pytest.raises(DescribeError):
        terse("banana")


def test_terse_is_deterministic():
    for expr in ("*/5 * * * *", "0 9 * * MON-FRI", "0 0 29 2 *", "17 3 1,15 6 0"):
        assert terse(expr) == terse(expr)


# --- CLI ----------------------------------------------------------------------

def test_cli_terse_acceptance_examples(capsys):
    cases = [
        ("*/5 * * * *", "every 5 min"),
        ("0 9 * * MON-FRI", "09:00 Mon-Fri"),
        ("30 14 1 * *", "14:30 dom-1"),
        ("0 9 * * *", "09:00 daily"),
    ]
    for expr, expected in cases:
        assert main(["--locale-style", "terse", expr]) == 0
        assert capsys.readouterr().out == expected + "\n"


def test_cli_unknown_style_exits_2(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--locale-style", "klingon", "* * * * *"])
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_cli_default_output_unchanged(capsys):
    assert main(["*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "Every 5 minutes\n"


def test_cli_plain_style_matches_default(capsys):
    assert main(["--locale-style", "plain", "0 9 * * MON-FRI"]) == 0
    assert capsys.readouterr().out == "At 09:00, Monday through Friday\n"


def test_cli_terse_invalid_expression_exit_code(capsys):
    assert main(["--locale-style", "terse", "90 * * * *"]) == 2
    assert "error:" in capsys.readouterr().err
