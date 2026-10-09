"""Tests for --locale-style terse (issue #4)."""
import pytest

from cronlish.locale import terse
from cronlish.describe import DescribeError


def test_terse_every_five_min():
    assert terse("*/5 * * * *") == "every 5 min"


def test_terse_weekday_mornings():
    assert terse("0 9 * * MON-FRI") == "09:00 Mon-Fri"


def test_terse_monthly_afternoon():
    assert terse("30 14 1 * *") == "14:30 dom-1"


def test_terse_daily_clock():
    assert terse("0 9 * * *") == "09:00 daily"


def test_terse_deterministic():
    assert terse("0 9 * * MON-FRI") == terse("0 9 * * MON-FRI")


def test_cli_locale_style_terse(capsys):
    from cronlish.cli import main

    assert main(["--locale-style", "terse", "*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "every 5 min\n"


def test_cli_locale_style_weekday(capsys):
    from cronlish.cli import main

    assert main(["--locale-style", "terse", "0 9 * * MON-FRI"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


def test_cli_default_unchanged(capsys):
    from cronlish.cli import main

    assert main(["*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "Every 5 minutes\n"


def test_cli_unknown_locale_style_exits_2():
    from cronlish.cli import main

    with pytest.raises(SystemExit) as exc:
        main(["--locale-style", "klingon", "*/5 * * * *"])
    assert exc.value.code == 2
