"""Terse CLI contract and calendar/validation regressions."""
import pytest

from cronlish import DescribeError, describe
from cronlish.cli import main
from cronlish.locale import terse


@pytest.mark.parametrize("expr,expected", [
    ("*/5 * * * *", "every 5 min"),
    ("0 9 * * MON-FRI", "09:00 Mon-Fri"),
    ("30 14 1 * *", "14:30 dom-1"),
    ("0 9 * * *", "09:00 daily"),
    ("* * * * *", "every min"),
    ("*/7 * * * *", "min-0,7,14,21,28,35,42,49,56 hourly"),
    ("0,30 * * * *", "every 30 min"),
    ("10-20/5 9-17 * * *", "min-10,15,20 hour-09-17"),
    ("* 9 * * *", "every min hour-09"),
    ("0 9 1 1 MON", "09:00 (dom-1 or Mon) Jan"),
    ("0 9 1,15 1-3 *", "09:00 dom-1,15 Jan-Mar"),
    ("0 9 * 3,6,9 SAT,SUN", "09:00 Sun,Sat Mar,Jun,Sep"),
    ("0 9 * * 0,7", "09:00 Sun"),
    ("0 9 * * 0-7", "09:00 daily"),
    ("0 9 1-5/2 * */2", "09:00 (dom-1,3,5 or Sun,Tue,Thu,Sat)"),
    ("  */5   *\t* * * ", "every 5 min"),
    ("@hourly", "every 60 min"),
    ("@DAILY", "00:00 daily"),
    ("@midnight", "00:00 daily"),
    ("@weekly", "00:00 Sun"),
    ("@monthly", "00:00 dom-1"),
    ("@yearly", "00:00 dom-1 Jan"),
    ("@annually", "00:00 dom-1 Jan"),
])
def test_terse_cli_and_api(expr, expected, capsys):
    assert terse(expr) == expected
    assert main(["--locale-style", "terse", expr]) == 0
    output = capsys.readouterr()
    assert output.out == expected + "\n"
    assert output.err == ""
    assert main([expr]) == 0
    assert capsys.readouterr().out == describe(expr) + "\n"


@pytest.mark.parametrize("expr", ["", "@unknown", "* * * *", "* * * * * *",
    "60 * * * *", "0 24 * * *", "*/0 * * * *", "0 9 * JAN *",
    "0 9 * * FRI-MON", "0,,1 * * * *", "0 9 0 * *"])
def test_same_validation_as_default(expr, capsys):
    with pytest.raises(DescribeError) as default:
        describe(expr)
    with pytest.raises(DescribeError) as compact:
        terse(expr)
    assert str(compact.value) == str(default.value)
    assert main(["--locale-style", "terse", expr]) == 2
    result = capsys.readouterr()
    assert result.out == ""
    assert result.err == f"error: {default.value}\n"


def test_unknown_style(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--locale-style", "klingon", "* * * * *"])
    assert exc.value.code == 2
    result = capsys.readouterr()
    assert result.out == ""
    assert "--locale-style" in result.err
    assert "invalid choice" in result.err
    assert "terse" in result.err


def test_split_expression(capsys):
    assert main(["--locale-style", "terse", "0", "9", "*", "*", "MON-FRI"]) == 0
    assert capsys.readouterr().out == "09:00 Mon-Fri\n"


def test_equivalent_inputs_are_deterministic():
    expressions = ["0 9 * * MON-FRI", "0 9 * * 1-5", "0 9 * * 5,3,2,4,1,1"]
    assert {terse(expr) for expr in expressions} == {"09:00 Mon-Fri"}
