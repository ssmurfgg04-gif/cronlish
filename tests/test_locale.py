"""Contracts for compact output, shared validation, and the real CLI."""
import os
import subprocess
import sys

import pytest

from cronlish import DescribeError, describe, terse
from cronlish.cli import main


@pytest.mark.parametrize("expr, expected", [
    ("*/5 * * * *", "every 5 min"),
    ("0 9 * * MON-FRI", "09:00 Mon-Fri"),
    ("30 14 1 * *", "14:30 dom-1"),
    ("0 9 * * *", "09:00 daily"),
])
def test_required_examples_exact(expr, expected, capsys):
    assert terse(expr) == expected
    assert main(["--locale-style", "terse", expr]) == 0
    captured = capsys.readouterr()
    assert captured.out == expected + "\n"
    assert captured.err == ""


@pytest.mark.parametrize("expr, expected", [
    ("* * * * *", "every min"),
    ("*/1 * * * *", "every min"),
    ("30 * * * *", "min-30 hourly"),
    ("*/5 9 * * *", "every 5 min hour-9"),
    ("5,20,45 9,12,18 * * *", "min-5,20,45 hour-9,12,18"),
    ("10-20/5 */6 * * *", "min-10,15,20 hour-0,6,12,18"),
    ("0 5 1-7 * *", "05:00 dom-1-7"),
    ("0 9 1 * MON", "09:00 dom-1|Mon"),
    ("0 9 1 1 MON", "09:00 dom-1|Mon mon-Jan"),
    ("0 9 * 3,6,9 MON-FRI", "09:00 Mon-Fri mon-Mar,Jun,Sep"),
    ("0 0 * 1-3 *", "00:00 mon-Jan-Mar"),
    ("* 9-17 * * *", "every min hour-9-17"),
    ("0 0 */2 */3 */2",
     "00:00 dom-1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31"
     "|Sun,Tue,Thu,Sat mon-Jan,Apr,Jul,Oct"),
    ("@hourly", "min-0 hourly"),
    ("@Daily", "00:00 daily"),
    ("@midnight", "00:00 daily"),
    ("@weekly", "00:00 Sun"),
    ("@monthly", "00:00 dom-1"),
    ("@yearly", "00:00 dom-1 mon-Jan"),
    ("@annually", "00:00 dom-1 mon-Jan"),
])
def test_supported_shapes_are_compact_and_deterministic(expr, expected):
    assert terse(expr) == expected


@pytest.mark.parametrize("left, right", [
    ("  */5   *\t* * *  ", "0,5,10,15,20,25,30,35,40,45,50,55 * * * *"),
    ("0 9 * * fri,mon,tue,wed,thu", "0 9 * * 1-5"),
    ("0 0 * * 7", "0 0 * * SUN"),
    ("0 0 * * 0,7", "0 0 * * 0"),
    ("0 9 * * 0-7", "0 9 * * *"),
    ("0 0 15,1,15 * *", "0 0 1,15 * *"),
])
def test_equivalent_schedules_have_byte_identical_terse_output(left, right):
    assert terse(left) == terse(right)


@pytest.mark.parametrize("expr", [
    "",
    "* * * *",
    "* * * * * *",
    "@sometimes",
    "@daily extra",
    "60 * * * *",
    "0 24 * * *",
    "0 0 0 * *",
    "0 0 * 13 *",
    "0 0 * * 8",
    "*/0 * * * *",
    "*/x * * * *",
    "5/2 * * * *",
    "50-10 * * * *",
    "0 0 * JAN *",
    "0 0 * * MONDAY",
    "0,,1 * * * *",
])
def test_validation_error_matches_default_renderer(expr):
    with pytest.raises(DescribeError) as default_error:
        describe(expr)
    with pytest.raises(DescribeError) as terse_error:
        terse(expr)
    assert str(terse_error.value) == str(default_error.value)


def test_flag_can_follow_unquoted_expression(capsys):
    assert main(["0", "9", "*", "*", "MON-FRI",
                 "--locale-style", "terse"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


def test_unknown_style_is_argparse_error(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--locale-style", "klingon", "* * * * *"])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid choice" in captured.err
    assert "klingon" in captured.err
    assert "terse" in captured.err


def test_cli_invalid_expression_returns_two(capsys):
    assert main(["--locale-style", "terse", "60 * * * *"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "field 1 (minute)" in captured.err


def test_default_cli_output_remains_byte_identical(capsys):
    assert main(["0 9 * * MON-FRI"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "At 09:00, Monday through Friday\n"
    assert captured.err == ""


def test_process_boundary_for_required_example():
    result = subprocess.run(
        [sys.executable, "-m", "cronlish.cli",
         "--locale-style", "terse", "0 9 * * MON-FRI"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "09:00 Mon-Fri\n"
    assert result.stderr == ""


def test_process_boundary_for_invalid_style():
    result = subprocess.run(
        [sys.executable, "-m", "cronlish.cli",
         "--locale-style", "klingon", "* * * * *"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "invalid choice" in result.stderr
    assert "klingon" in result.stderr


def test_separate_processes_are_byte_identical():
    command = [
        sys.executable, "-m", "cronlish.cli",
        "--locale-style", "terse", "0 9 1 1 MON",
    ]
    first = subprocess.run(
        command, capture_output=True, text=False, check=False,
    )
    second = subprocess.run(
        command, capture_output=True, text=False, check=False,
    )
    assert first.returncode == second.returncode == 0
    expected = ("09:00 dom-1|Mon mon-Jan" + os.linesep).encode()
    assert first.stdout == second.stdout == expected
    assert first.stderr == second.stderr == b""
