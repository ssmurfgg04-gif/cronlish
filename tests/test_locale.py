"""Exact terse descriptions and CLI regression coverage."""
import os
import subprocess
import sys

import pytest

from cronlish import DescribeError, describe
from cronlish.cli import main
from cronlish.locale import terse


EXAMPLES = [
    ("*/5 * * * *", "every 5 min"),
    ("0 9 * * MON-FRI", "09:00 Mon-Fri"),
    ("30 14 1 * *", "14:30 dom-1"),
    ("0 9 * * *", "09:00 daily"),
]


@pytest.mark.parametrize("expr, expected", EXAMPLES)
def test_required_outputs(expr, expected, capsys):
    assert terse(expr) == expected
    assert main(["--locale-style", "terse", expr]) == 0
    captured = capsys.readouterr()
    assert captured.out == expected + "\n"
    assert captured.err == ""


@pytest.mark.parametrize("expr, expected", [
    ("* * * * *", "every min"),
    ("*/1 * * * *", "every min"),
    ("5 4 * * *", "04:05 daily"),
    ("30 * * * *", "min-30"),
    ("0,30 * * * *", "min-0,30"),
    ("10-20 * * * *", "min-10-20"),
    ("10-20/5 * * * *", "min-10-20/5"),
    ("0 9,12,18 * * *", "min-0 hour-9,12,18"),
    ("* 9-17 * * *", "every min hour-9-17"),
    ("*/15 */2 * * *", "every 15 min hour-0-22/2"),
    ("*/5 9 * * *", "every 5 min hour-9"),
    ("0 0 1,15 * *", "00:00 dom-1,15"),
    ("0 0 */2 * *", "00:00 dom-1-31/2"),
    ("0 0 * 3,6,9 *", "00:00 Mar-Sep/3"),
    ("0 0 1 */3 *", "00:00 dom-1 Jan-Oct/3"),
    ("0 9 * * */2", "09:00 Sun-Sat/2"),
    ("0 9 * * SAT,SUN", "09:00 Sun,Sat"),
    ("0 9 * * 0-7", "09:00 daily"),
    ("0 9 1 * MON", "09:00 (dom-1 or Mon)"),
    ("0 9 1 1 MON", "09:00 (dom-1 or Mon) Jan"),
    ("0 9 * 1 MON", "09:00 Mon Jan"),
    ("@hourly", "min-0"),
    ("@daily", "00:00 daily"),
    ("@midnight", "00:00 daily"),
    ("@weekly", "00:00 Sun"),
    ("@monthly", "00:00 dom-1"),
    ("@yearly", "00:00 dom-1 Jan"),
    ("@annually", "00:00 dom-1 Jan"),
    ("  @DAILY\t", "00:00 daily"),
])
def test_supported_syntax(expr, expected):
    assert terse(expr) == expected


@pytest.mark.parametrize("left, right", [
    ("0 9 * * SUN", "0 9 * * 7"),
    ("0 9 * * 7,0,7", "0 9 * * 0"),
    ("0 9 * * MON-FRI", "  0  9 * * mon-fri  "),
    ("0,15,30,45 * * * *", "*/15 * * * *"),
    ("0 9,18,12,9 * * *", "0 12,9,18 * * *"),
    ("0 9 1-31 1-12 0-7", "0 9 * * *"),
])
def test_equivalent_expressions_are_deterministic(left, right):
    assert terse(left) == terse(right)


@pytest.mark.parametrize("expr", [
    "", "banana", "* * * *", "* * * * * *", "@sometimes",
    "60 * * * *", "0 24 * * *", "0 0 0 * *", "0 0 * 13 *",
    "0 0 * * 8", "0 0 * JAN *", "*/0 * * * *", "*/x * * * *",
    "50-10 * * * *", "0,,30 * * * *", "5/2 * * * *",
])
def test_validation_matches_default(expr, capsys):
    with pytest.raises(DescribeError) as default:
        describe(expr)
    with pytest.raises(DescribeError) as compact:
        terse(expr)
    assert str(compact.value) == str(default.value)
    assert main(["--locale-style", "terse", expr]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"error: {default.value}\n"


@pytest.mark.parametrize("expr, expected", [
    ("*/5 * * * *", "Every 5 minutes\n"),
    ("0 9 * * MON-FRI", "At 09:00, Monday through Friday\n"),
    ("30 14 1 * *", "At 14:30 on day 1 of the month\n"),
    ("0 9 * * *", "At 09:00 every day\n"),
    ("@hourly", "At minute 0 past every hour\n"),
])
def test_default_cli_bytes_unchanged(expr, expected, capsys):
    assert main([expr]) == 0
    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""


def test_unquoted_expression_and_trailing_flag(capsys):
    assert main(["0", "9", "*", "*", "MON-FRI", "--locale-style", "terse"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


@pytest.mark.parametrize("args", [
    ["--locale-style", "klingon", "0 9 * * *"],
    ["--locale-style"],
    ["--locale-style", "terse"],
])
def test_argument_errors(args, capsys):
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err
    if "klingon" in args:
        assert "invalid choice: 'klingon'" in captured.err
        assert "terse" in captured.err


def test_help_documents_style(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "--locale-style {terse}" in capsys.readouterr().out


@pytest.mark.parametrize("seed", ["1", "123"])
def test_process_output_is_stable(seed):
    result = subprocess.run(
        [sys.executable, "-m", "cronlish.cli", "--locale-style", "terse",
         "0 9 15,1,15 3,1 MON,FRI"],
        env={**os.environ, "PYTHONHASHSEED": seed},
        capture_output=True, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == b"09:00 (dom-1,15 or Mon,Fri) Jan,Mar\n"
    assert result.stderr == b""


def test_module_cli_unknown_style():
    result = subprocess.run(
        [sys.executable, "-m", "cronlish.cli", "--locale-style", "klingon",
         "0 9 * * *"], capture_output=True, check=False,
    )
    assert result.returncode == 2
    assert result.stdout == b""
    assert b"invalid choice: 'klingon'" in result.stderr
