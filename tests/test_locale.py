"""Terse output, shared cron semantics, and the CLI's observable behavior."""
import subprocess
import sys

import pytest

from cronlish import DescribeError, describe
from cronlish.cli import main
from cronlish.locale import terse


@pytest.mark.parametrize("expr, expected", [
    ("*/5 * * * *", "every 5 min"),
    ("0 9 * * MON-FRI", "09:00 Mon-Fri"),
    ("30 14 1 * *", "14:30 dom-1"),
    ("0 9 * * *", "09:00 daily"),
])
def test_cli_exact_examples(expr, expected, capsys):
    assert main(["--locale-style", "terse", expr]) == 0
    captured = capsys.readouterr()
    assert captured.out == expected + "\n"
    assert captured.err == ""


@pytest.mark.parametrize("expr, expected", [
    ("* * * * *", "every min"),
    ("5 4 * * *", "04:05 daily"),
    ("30 * * * *", "min-30 hourly"),
    ("10-20/5 * * * *", "min-10-20/5 hourly"),
    ("0,30 9,17 * * *", "min-0,30 hour-9,17"),
    ("* 9-17 * * *", "every min hour-9-17"),
    ("*/15 */2 * * *", "every 15 min hour-0-22/2"),
    ("0 9 1,15 * *", "09:00 dom-1,15"),
    ("0 9 1-10/2 * *", "09:00 dom-1-9/2"),
    ("0 9 */2 * *", "09:00 dom-1-31/2"),
    ("0 9 * 1-3 *", "09:00 in Jan-Mar"),
    ("0 9 * */3 *", "09:00 in Jan,Apr,Jul,Oct"),
    ("0 9 * * */2", "09:00 Sun,Tue,Thu,Sat"),
    ("0 9 1 * MON", "09:00 (dom-1 or Mon)"),
    ("0 9 1 1 MON", "09:00 (dom-1 or Mon) in Jan"),
    ("*/5 * 1-3 3,6 MON-FRI", "every 5 min (dom-1-3 or Mon-Fri) in Mar,Jun"),
    ("@hourly", "min-0 hourly"),
    ("@daily", "00:00 daily"),
    ("@midnight", "00:00 daily"),
    ("@weekly", "00:00 Sun"),
    ("@monthly", "00:00 dom-1"),
    ("@yearly", "00:00 dom-1 in Jan"),
    ("@annually", "00:00 dom-1 in Jan"),
])
def test_terse_supported_syntax(expr, expected):
    assert terse(expr) == expected


@pytest.mark.parametrize("expr, equivalent", [
    ("  0  9 * * mon-fri  ", "0 9 * * 1-5"),
    ("0 9 * * 0,7,SUN", "0 9 * * SUN"),
    ("0 9 * * SAT,SUN", "0 9 * * 0,6"),
    ("0 9 1-31 1-12 0-7", "0 9 * * *"),
    ("45,0,30,15 * * * *", "*/15 * * * *"),
    (" @DAILY ", "0 0 * * *"),
])
def test_equivalent_inputs_are_canonical(expr, equivalent):
    assert terse(expr) == terse(equivalent)
    assert terse(expr) == terse(expr)


@pytest.mark.parametrize("expr", [
    "", "* * * *", "* * * * * *", "@sometimes", "@daily extra",
    "60 * * * *", "0 24 * * *", "0 0 0 * *", "0 0 * 13 *",
    "0 0 * * 8", "*/0 * * * *", "10-5 * * * *", "0,,5 * * * *",
    "0 0 * JAN *",
])
def test_terse_preserves_validation(expr):
    with pytest.raises(DescribeError) as full:
        describe(expr)
    with pytest.raises(DescribeError) as compact:
        terse(expr)
    assert str(compact.value) == str(full.value)


def test_cli_terse_unquoted_fields_and_trailing_flag(capsys):
    assert main(["0", "9", "*", "*", "MON-FRI", "--locale-style", "terse"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


@pytest.mark.parametrize("expr", ["*/5 * * * *", "0 9 * * MON-FRI", "@daily"])
def test_cli_default_output_is_unchanged(expr, capsys):
    assert main([expr]) == 0
    assert capsys.readouterr().out == describe(expr) + "\n"


@pytest.mark.parametrize("args, diagnostic", [
    (["--locale-style", "klingon", "0 9 * * *"], "invalid choice"),
    (["--locale-style"], "expected one argument"),
    (["--locale-style", "terse", "90 * * * *"], "out of range 0-59"),
    (["--locale-style", "terse"], "expression"),
])
def test_cli_process_errors(args, diagnostic):
    result = subprocess.run([sys.executable, "-m", "cronlish.cli", *args],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert result.stdout == ""
    assert diagnostic in result.stderr


def test_cli_help_documents_style(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "--locale-style {terse}" in capsys.readouterr().out
