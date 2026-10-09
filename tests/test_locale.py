"""Tests for cronlish.locale and --locale-style CLI integration."""
import subprocess
import sys

import pytest

from cronlish import DescribeError, describe, terse
from cronlish.cli import main


# --- Acceptance criteria exact examples ---------------------------------------

SPEC_EXAMPLES = [
    ("*/5 * * * *", "every 5 min"),
    ("0 9 * * MON-FRI", "09:00 Mon-Fri"),
    ("30 14 1 * *", "14:30 dom-1"),
    ("0 9 * * *", "09:00 daily"),
]


@pytest.mark.parametrize("expr, expected", SPEC_EXAMPLES)
def test_spec_examples_api(expr, expected):
    assert terse(expr) == expected


@pytest.mark.parametrize("expr, expected", SPEC_EXAMPLES)
def test_spec_examples_cli(expr, expected, capsys):
    assert main(["--locale-style", "terse", expr]) == 0
    captured = capsys.readouterr()
    assert captured.out == expected + "\n"
    assert captured.err == ""


# --- CLI flag behavior and errors ---------------------------------------------

def test_cli_invalid_locale_style_exits_two(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--locale-style", "klingon", "0 9 * * *"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid choice" in captured.err
    assert "klingon" in captured.err
    assert "terse" in captured.err


def test_cli_without_flag_preserves_default_output(capsys):
    assert main(["*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "Every 5 minutes\n"

    assert main(["0 9 * * MON-FRI"]) == 0
    assert capsys.readouterr().out == "At 09:00, Monday through Friday\n"

    assert main(["30 14 1 * *"]) == 0
    assert capsys.readouterr().out == "At 14:30 on day 1 of the month\n"

    assert main(["0 9 * * *"]) == 0
    assert capsys.readouterr().out == "At 09:00 every day\n"


def test_cli_unquoted_expression_with_terse_flag(capsys):
    assert main(["--locale-style", "terse", "0", "9", "*", "*", "MON-FRI"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


def test_cli_flag_after_expression(capsys):
    assert main(["0 9 * * *", "--locale-style", "terse"]) == 0
    assert capsys.readouterr().out == "09:00 daily\n"


def test_cli_invalid_expression_with_terse_flag(capsys):
    assert main(["--locale-style", "terse", "90 * * * *"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err
    assert "out of range 0-59" in captured.err


def test_cli_subprocess_execution():
    result = subprocess.run(
        [sys.executable, "-m", "cronlish.cli", "--locale-style", "terse", "0 9 * * MON-FRI"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "09:00 Mon-Fri\n"
    assert result.stderr == ""

    bad_style = subprocess.run(
        [sys.executable, "-m", "cronlish.cli", "--locale-style", "klingon", "0 9 * * *"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad_style.returncode == 2
    assert "invalid choice" in bad_style.stderr


# --- Supported syntax and deterministic output --------------------------------

@pytest.mark.parametrize("expr, expected", [
    ("* * * * *", "every min"),
    ("*/1 * * * *", "every min"),
    ("0-59 * * * *", "every min"),
    ("30 * * * *", "min-30 hourly"),
    ("0,30 * * * *", "min-0,30 hourly"),
    ("10-20 * * * *", "min-10-20 hourly"),
    ("10-20/5 * * * *", "min-10,15,20 hourly"),
    ("5 4 * * *", "04:05 daily"),
    ("* 9-17 * * *", "every min hour-9-17"),
    ("*/5 9 * * *", "every 5 min hour-9"),
    ("30 9-17 * * *", "min-30 hour-9-17"),
    ("0 9,12,18 * * *", "min-0 hour-9,12,18"),
    ("0 */6 * * *", "min-0 hour-0,6,12,18"),
    ("*/15 */2 * * *", "every 15 min hour-0,2,4,6,8,10,12,14,16,18,20,22"),
    ("0 0 * * 0", "00:00 Sun"),
    ("0 0 * * 7", "00:00 Sun"),
    ("0 12 * * WED", "12:00 Wed"),
    ("0 12 * * sat", "12:00 Sat"),
    ("30 8 * * SAT,SUN", "08:30 Sun,Sat"),
    ("0 0 * * 0-6", "00:00 daily"),
    ("0 9 * * */2", "09:00 Sun,Tue,Thu,Sat"),
    ("0 5 1-7 * *", "05:00 dom-1-7"),
    ("0 5 1,15 * *", "05:00 dom-1,15"),
    ("0 0 1,3,5 * *", "00:00 dom-1,3,5"),
    ("0 0 1 1 *", "00:00 dom-1 month-Jan"),
    ("0 0 * 1-3 *", "00:00 month-Jan-Mar"),
    ("0 0 * 3,6,9 *", "00:00 month-Mar,Jun,Sep"),
    ("0 9 1 * 1", "09:00 dom-1 or Mon"),
    ("0 9 1 1 1", "09:00 (dom-1 or Mon) month-Jan"),
    ("@hourly", "min-0 hourly"),
    ("@daily", "00:00 daily"),
    ("@midnight", "00:00 daily"),
    ("@weekly", "00:00 Sun"),
    ("@monthly", "00:00 dom-1"),
    ("@yearly", "00:00 dom-1 month-Jan"),
    ("@annually", "00:00 dom-1 month-Jan"),
    ("  */5   *\t*  * * ", "every 5 min"),
])
def test_terse_supported_syntax(expr, expected):
    assert terse(expr) == expected


@pytest.mark.parametrize("left, right", [
    ("  */5   *\t* * *  ", "0,5,10,15,20,25,30,35,40,45,50,55 * * * *"),
    ("0 9 * * fri,mon,tue,wed,thu", "0 9 * * 1-5"),
    ("0 0 * * 7", "0 0 * * SUN"),
    ("0 0 * * 0,7", "0 0 * * 0"),
    ("0 9 * * 0-7", "0 9 * * *"),
    ("0 0 15,1,15 * *", "0 0 1,15 * *"),
])
def test_terse_deterministic_canonical(left, right):
    assert terse(left) == terse(right)
    assert terse(left) == terse(left)


# --- Error propagation matching describe --------------------------------------

@pytest.mark.parametrize("expr", [
    "",
    "*/5 * * *",
    "* * * * * *",
    "banana * * * *",
    "*/0 * * * *",
    "*/x * * * *",
    "5/2 * * * *",
    "60 * * * *",
    "0 24 * * *",
    "0 0 0 * *",
    "0 0 1 13 *",
    "0 0 * * 8",
    "50-10 * * * *",
    "0 0 1 JAN *",
    "@sometimes",
    "MONDAY * * * *",
])
def test_terse_shares_describe_validation(expr):
    with pytest.raises(DescribeError) as desc_err:
        describe(expr)
    with pytest.raises(DescribeError) as terse_err:
        terse(expr)
    assert str(desc_err.value) == str(terse_err.value)
