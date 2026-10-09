"""Terse output contracts and real CLI regression/error paths."""
import subprocess
import sys

import pytest

from cronlish import DescribeError, describe
from cronlish.cli import main


EXAMPLES = [
    ("*/5 * * * *", "every 5 min"),
    ("0 9 * * MON-FRI", "09:00 Mon-Fri"),
    ("30 14 1 * *", "14:30 dom-1"),
    ("0 9 * * *", "09:00 daily"),
]


@pytest.mark.parametrize("expr,expected", EXAMPLES)
def test_terse_cli_exact_examples(expr, expected, capsys):
    assert main(["--locale-style", "terse", expr]) == 0
    captured = capsys.readouterr()
    assert captured.out == expected + "\n"
    assert captured.err == ""


@pytest.mark.parametrize("expr,expected", EXAMPLES + [
    ("* * * * *", "every min"),
    ("30 * * * *", "min-30 hourly"),
    ("* 9 * * *", "every min h-9"),
    ("*/5 9 * * *", "every 5 min h-9"),
    ("0 */6 * * *", "min-0 h-*/6"),
    ("10-20/5 9,12 * * *", "min-10-20/5 h-9,12"),
    ("0 5 1-7 * *", "05:00 dom-1-7"),
    ("0 5 1,15 * *", "05:00 dom-1,15"),
    ("0 0 1 */3 *", "00:00 dom-1 in-Jan,Apr,Jul,Oct"),
    ("0 0 * 1-3 *", "00:00 in-Jan-Mar"),
    ("0 9 1 * MON", "09:00 (dom-1 or Mon)"),
    ("0 9 1 3 MON", "09:00 (dom-1 or Mon) in-Mar"),
    ("0 9 * * */2", "09:00 Sun,Tue,Thu,Sat"),
    ("0 9 * * SAT,SUN", "09:00 Sun,Sat"),
    ("0 9 */2 * *", "09:00 dom-*/2"),
])
def test_terse_public_api(expr, expected):
    from cronlish.locale import terse

    assert terse(expr) == expected


@pytest.mark.parametrize("macro,expected", [
    ("@hourly", "min-0 hourly"),
    ("@daily", "00:00 daily"),
    ("@midnight", "00:00 daily"),
    ("@weekly", "00:00 Sun"),
    ("@monthly", "00:00 dom-1"),
    ("@yearly", "00:00 dom-1 in-Jan"),
    ("@annually", "00:00 dom-1 in-Jan"),
    (" @DaIlY ", "00:00 daily"),
])
def test_terse_macros(macro, expected):
    from cronlish.locale import terse

    assert terse(macro) == expected


@pytest.mark.parametrize("expr", [
    "", "* * * *", "60 * * * *", "*/0 * * * *", "0 9 * * FRI-MON",
    "0 0 1 JAN *", "@sometimes", "0,,30 * * * *",
])
def test_terse_shares_field_specific_validation(expr):
    from cronlish.locale import terse

    with pytest.raises(DescribeError) as standard:
        describe(expr)
    with pytest.raises(DescribeError) as compact:
        terse(expr)
    assert str(compact.value) == str(standard.value)


@pytest.mark.parametrize("left,right", [
    ("0,15,30,45 * * * *", "*/15 * * * *"),
    ("0 9 * * 7", "0 9 * * SUN"),
    ("0 9 * * fri,MON,mon", "0 9 * * MON,FRI"),
    ("0 9 * * 0-6", "0 9 * * *"),
    ("0 9 1-31 * *", "0 9 * * *"),
])
def test_terse_is_canonical_and_deterministic(left, right):
    from cronlish.locale import terse

    assert terse(left) == terse(right) == terse(left)


@pytest.mark.parametrize("expr,expected", [
    ("*/5 * * * *", "Every 5 minutes"),
    ("0 9 * * MON-FRI", "At 09:00, Monday through Friday"),
    ("30 14 1 * *", "At 14:30 on day 1 of the month"),
    ("0 9 1 * MON", "At 09:00 on day 1 of the month or on Monday"),
    ("@daily", "At 00:00 every day"),
])
def test_default_cli_bytes_unchanged(expr, expected, capsys):
    assert main([expr]) == 0
    assert capsys.readouterr().out == expected + "\n"


def test_unknown_style_is_an_argparse_choice_error(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--locale-style", "klingon", "0 9 * * *"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid choice" in captured.err
    assert "klingon" in captured.err
    assert "terse" in captured.err


def test_terse_invalid_expression_returns_two(capsys):
    assert main(["--locale-style", "terse", "90 * * * *"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "out of range 0-59" in captured.err


def test_terse_cli_unquoted_fields(capsys):
    assert main(["--locale-style", "terse", "0", "9", "*", "*", "MON-FRI"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


def test_terse_flag_after_expression(capsys):
    assert main(["0 9 * * *", "--locale-style", "terse"]) == 0
    assert capsys.readouterr().out == "09:00 daily\n"


@pytest.mark.parametrize("args,code,stdout,error", [
    (["--locale-style", "terse", "0 9 * * *"], 0, "09:00 daily\n", ""),
    (["--locale-style", "klingon", "0 9 * * *"], 2, "", "invalid choice"),
    (["--locale-style", "terse", "90 * * * *"], 2, "", "out of range 0-59"),
])
def test_real_cli_process(args, code, stdout, error):
    result = subprocess.run(
        [sys.executable, "-m", "cronlish.cli", *args],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == code
    assert result.stdout == stdout
    assert error in result.stderr
