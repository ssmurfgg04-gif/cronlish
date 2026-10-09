"""Tests for compact output and the opt-in CLI flag."""
import pytest

from cronlish import DescribeError, describe
from cronlish.cli import main
from cronlish.locale import terse


def test_terse_every_five_minutes():
    assert terse("*/5 * * * *") == "every 5 min"


def test_terse_weekday_mornings():
    assert terse("0 9 * * MON-FRI") == "09:00 Mon-Fri"


def test_terse_monthly_afternoon():
    assert terse("30 14 1 * *") == "14:30 dom-1"


def test_terse_daily_clock():
    assert terse("0 9 * * *") == "09:00 daily"


def test_cli_terse_every_five_minutes(capsys):
    assert main(["--locale-style", "terse", "*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "every 5 min\n"


def test_cli_terse_weekday_mornings(capsys):
    assert main(["--locale-style", "terse", "0 9 * * MON-FRI"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


def test_cli_terse_monthly_afternoon(capsys):
    assert main(["--locale-style", "terse", "30 14 1 * *"]) == 0
    assert capsys.readouterr().out == "14:30 dom-1\n"


def test_cli_terse_daily_clock(capsys):
    assert main(["--locale-style", "terse", "0 9 * * *"]) == 0
    assert capsys.readouterr().out == "09:00 daily\n"


def test_cli_unknown_locale_style(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--locale-style", "klingon", "0 9 * * *"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid choice: 'klingon'" in captured.err
    assert "terse" in captured.err


def test_terse_is_deterministic(capsys):
    for expr in ("*/5 * * * *", "0 9 * * MON-FRI", "30 14 1 * *",
                 "0 9 * * *", "0 9 1 1 MON", "0,30 9,12 * * SAT,SUN"):
        expected = terse(expr).encode("utf-8")
        for _ in range(3):
            assert terse(expr).encode("utf-8") == expected
            assert main(["--locale-style", "terse", expr]) == 0
            assert capsys.readouterr().out.encode("utf-8") == expected + b"\n"


def test_cli_defaults_remain_byte_identical(capsys):
    for expr, expected in (
        ("*/5 * * * *", b"Every 5 minutes\n"),
        ("0 9 * * MON-FRI", b"At 09:00, Monday through Friday\n"),
        ("30 14 1 * *", b"At 14:30 on day 1 of the month\n"),
        ("0 9 * * *", b"At 09:00 every day\n"),
    ):
        assert main([expr]) == 0
        assert capsys.readouterr().out.encode("utf-8") == expected


def test_cli_terse_unquoted_expression(capsys):
    assert main(["--locale-style", "terse", "*/5", "*", "*", "*", "*"]) == 0
    assert capsys.readouterr().out == "every 5 min\n"


def test_terse_macro_and_whitespace():
    assert terse("  @Daily  ") == "00:00 daily"
    assert terse("  0  9 * * mon-fri  ") == "09:00 Mon-Fri"


def test_terse_lists_ranges_and_steps():
    assert terse("0,15,30,45 * * * *") == "every 15 min"
    assert terse("10-20/5 9-17 1,15 * *") == "min-10,15,20 hr-9-17 dom-1,15"
    assert terse("0 9 * * SAT,SUN") == "09:00 Sun,Sat"
    assert terse("0 */6 * * *") == "min-0 every 6 hr"


def test_terse_day_fields_are_ored():
    assert terse("0 9 1 * MON") == "09:00 dom-1 or Mon"
    assert terse("0 9 1 1 MON") == "09:00 (dom-1 or Mon) month-Jan"


def test_terse_sunday_and_full_week():
    assert terse("0 9 * * 7") == "09:00 Sun"
    assert terse("0 9 * * 0-6") == "09:00 daily"


def test_terse_validation_matches_default():
    for expr in ("", "90 * * * *", "*/0 * * * *", "@sometimes", "0 0 1 JAN *"):
        with pytest.raises(DescribeError) as original:
            describe(expr)
        with pytest.raises(DescribeError) as compact:
            terse(expr)
        assert str(compact.value) == str(original.value)


def test_cli_terse_invalid_expression(capsys):
    assert main(["--locale-style", "terse", "90 * * * *"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "out of range 0-59" in captured.err
