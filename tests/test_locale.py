"""Tests for cronlish.locale.terse and the --locale-style CLI flag."""
import pytest

from cronlish import DescribeError
from cronlish.cli import main as cli_main
from cronlish.locale import terse


# --- the four examples from the issue spec -----------------------------------

def test_terse_every_five_minutes():
    assert terse("*/5 * * * *") == "every 5 min"


def test_terse_weekday_mornings():
    assert terse("0 9 * * MON-FRI") == "09:00 Mon-Fri"


def test_terse_monthly_afternoon():
    assert terse("30 14 1 * *") == "14:30 dom-1"


def test_terse_daily():
    assert terse("0 9 * * *") == "09:00 daily"


# --- determinism and error behavior -------------------------------------------

def test_terse_is_deterministic():
    assert terse("0 9 * * MON-FRI") == terse("0 9 * * MON-FRI")
    assert terse("*/15 * * * *") == "every 15 min"


def test_terse_macros():
    assert terse("@daily") == "00:00 daily"


def test_terse_invalid_expression_raises():
    with pytest.raises(DescribeError):
        terse("not a cron expression")


# --- CLI flag ------------------------------------------------------------------

def test_cli_terse_flag(capsys):
    assert cli_main(["--locale-style", "terse", "*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "every 5 min\n"


def test_cli_terse_flag_all_spec_examples(capsys):
    cases = {
        "*/5 * * * *": "every 5 min",
        "0 9 * * MON-FRI": "09:00 Mon-Fri",
        "30 14 1 * *": "14:30 dom-1",
        "0 9 * * *": "09:00 daily",
    }
    for expr, expected in cases.items():
        assert cli_main(["--locale-style", "terse", expr]) == 0
        assert capsys.readouterr().out == expected + "\n"


def test_cli_default_output_unchanged(capsys):
    assert cli_main(["*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "Every 5 minutes\n"


def test_cli_unknown_style_exits_2(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_main(["--locale-style", "klingon", "*/5 * * * *"])
    assert exc_info.value.code == 2
    assert "klingon" in capsys.readouterr().err
