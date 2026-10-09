"""Terse API and CLI behavior, including default-output compatibility."""
import pytest

from cronlish import DescribeError, describe
from cronlish.cli import main
from cronlish.locale import terse


EXAMPLES = [
    ("*/5 * * * *", "every 5 min", "Every 5 minutes"),
    ("0 9 * * MON-FRI", "09:00 Mon-Fri", "At 09:00, Monday through Friday"),
    ("30 14 1 * *", "14:30 dom-1", "At 14:30 on day 1 of the month"),
    ("0 9 * * *", "09:00 daily", "At 09:00 every day"),
]


@pytest.mark.parametrize("expr,compact,default", EXAMPLES)
def test_terse_examples(expr, compact, default, capsys):
    assert terse(expr) == compact
    assert main(["--locale-style", "terse", expr]) == 0
    output = capsys.readouterr()
    assert output.out == compact + "\n"
    assert output.err == ""


@pytest.mark.parametrize("expr,compact,default", EXAMPLES)
def test_default_cli_output_unchanged(expr, compact, default, capsys):
    assert main([expr]) == 0
    output = capsys.readouterr()
    assert output.out == default + "\n"
    assert output.err == ""


def test_terse_unquoted_expression_and_trailing_flag(capsys):
    assert main(["0", "9", "*", "*", "MON-FRI", "--locale-style", "terse"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


def test_unknown_style_uses_argparse_error(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--locale-style", "klingon", "* * * * *"])
    assert exc.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "--locale-style" in output.err
    assert "invalid choice" in output.err
    assert "klingon" in output.err
    assert "terse" in output.err


def test_terse_cli_bad_expression(capsys):
    assert main(["--locale-style", "terse", "90 * * * *"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "error:" in output.err
    assert "out of range 0-59" in output.err


@pytest.mark.parametrize("expr,expected", [
    ("* * * * *", "every min"),
    ("5 4 * * *", "04:05 daily"),
    ("30 * * * *", "min-30 hourly"),
    ("0,30 * * * *", "min-0,30 hourly"),
    ("10-20 * * * *", "min-10-20 hourly"),
    ("10-20/5 * * * *", "min-10,15,20 hourly"),
    ("*/45 * * * *", "min-0,45 hourly"),
    ("*/7 * * * *", "min-0,7,14,21,28,35,42,49,56 hourly"),
    ("30 9-17 * * *", "min-30 hour-9-17"),
    ("* 9 * * *", "min-* hour-9"),
    ("*/15 */6 * * *", "min-0,15,30,45 hour-0,6,12,18"),
    ("0 9 1,15 * *", "09:00 dom-1,15"),
    ("0 9 1-7 * *", "09:00 dom-1-7"),
    ("0 9 1-10/2 * *", "09:00 dom-1,3,5,7,9"),
    ("0 9 * * */2", "09:00 Sun,Tue,Thu,Sat"),
    ("0 9 * * SAT,SUN", "09:00 Sun,Sat"),
    ("0 9 * 1-3 *", "09:00 daily Jan-Mar"),
    ("0 9 1 */3 *", "09:00 dom-1 Jan,Apr,Jul,Oct"),
    ("0 9 1 * MON", "09:00 (dom-1 or Mon)"),
    ("0 9 1 1 MON-FRI", "09:00 (dom-1 or Mon-Fri) Jan"),
    ("@hourly", "min-0 hourly"),
    ("@daily", "00:00 daily"),
    ("@midnight", "00:00 daily"),
    ("@weekly", "00:00 Sun"),
    ("@monthly", "00:00 dom-1"),
    ("@yearly", "00:00 dom-1 Jan"),
    ("@annually", "00:00 dom-1 Jan"),
])
def test_supported_syntax(expr, expected):
    assert terse(expr) == expected


@pytest.mark.parametrize("expr,equivalent", [
    ("  */5   *\t* * *  ", "*/5 * * * *"),
    ("0 9 * * mon-fri", "0 9 * * 1-5"),
    ("0 9 * * 7,0,MON,1", "0 9 * * 0,1"),
    ("0 9 * * 0-7", "0 9 * * *"),
    ("45,0,15,30,15 * * * *", "*/15 * * * *"),
    ("@DAILY", "0 0 * * *"),
])
def test_equivalent_inputs_have_identical_output(expr, equivalent):
    assert terse(expr) == terse(equivalent)
    assert terse(expr) == terse(expr)


@pytest.mark.parametrize("expr", [
    "", "* * * *", "* * * * * *", "@sometimes", "@daily * * * *",
    "*/0 * * * *", "5/2 * * * *", "0 0 1 JAN *", "0 0 * * 8",
    "0,,30 * * * *", "0 24 * * *", "50-10 * * * *",
])
def test_terse_preserves_default_validation_errors(expr):
    with pytest.raises(DescribeError) as default:
        describe(expr)
    with pytest.raises(DescribeError) as compact:
        terse(expr)
    assert str(compact.value) == str(default.value)
