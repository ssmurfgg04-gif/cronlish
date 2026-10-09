"""Tests for cronlish.describe — every supported form plus error cases."""
import pytest

from cronlish import DescribeError, describe


# --- the three examples promised in the README ------------------------------

def test_readme_every_five_minutes():
    assert describe("*/5 * * * *") == "Every 5 minutes"


def test_readme_weekday_mornings():
    assert describe("0 9 * * MON-FRI") == "At 09:00, Monday through Friday"


def test_readme_monthly_afternoon():
    assert describe("30 14 1 * *") == "At 14:30 on day 1 of the month"


# --- minute and hour shapes ---------------------------------------------------

def test_every_minute_star():
    assert describe("* * * * *") == "Every minute"


def test_every_minute_step_one():
    assert describe("*/1 * * * *") == "Every minute"


def test_full_range_equals_star():
    assert describe("0-59 * * * *") == "Every minute"


def test_value_list_equivalent_to_step():
    assert describe("0,15,30,45 * * * *") == "Every 15 minutes"


def test_specific_minute_every_hour():
    assert describe("30 * * * *") == "At minute 30 past every hour"


def test_minute_range():
    assert describe("10-20 * * * *") == "At minutes 10 through 20 past every hour"


def test_minute_list_two():
    assert describe("0,30 * * * *") == "At minutes 0 and 30 past every hour"


def test_minute_list_three():
    assert describe("5,20,45 * * * *") == "At minutes 5, 20 and 45 past every hour"


def test_minute_partial_step_expands():
    assert describe("10-20/5 * * * *") == "At minutes 10, 15 and 20 past every hour"


def test_daily_clock_gets_filler():
    assert describe("0 0 * * *") == "At 00:00 every day"


def test_clock_zero_padding():
    assert describe("5 4 * * *") == "At 04:05 every day"


def test_hour_range():
    assert describe("30 9-17 * * *") == "At minute 30 past hours 9 through 17"


def test_hour_list():
    assert describe("0 9,12,18 * * *") == "At minute 0 past hours 9, 12 and 18"


def test_hour_step_full():
    assert describe("0 */6 * * *") == "At minute 0 past every 6 hours"


def test_hour_step_partial_expands():
    assert describe("15 0-20/2 * * *") == (
        "At minute 15 past hours 0, 2, 4, 6, 8, 10, 12, 14, 16, 18 and 20")


def test_both_fields_stepped():
    assert describe("*/15 */2 * * *") == "Every 15 minutes past every 2 hours"


def test_minute_step_with_fixed_hour():
    assert describe("*/5 9 * * *") == "Every 5 minutes past hour 9"


# --- day-of-week ---------------------------------------------------------------

def test_dow_sunday_zero():
    assert describe("0 0 * * 0") == "At 00:00, Sunday"


def test_dow_sunday_seven():
    assert describe("0 0 * * 7") == "At 00:00, Sunday"


def test_dow_name_single():
    assert describe("0 12 * * WED") == "At 12:00, Wednesday"


def test_dow_lowercase_name():
    assert describe("0 12 * * sat") == "At 12:00, Saturday"


def test_dow_list_of_names_sorted():
    assert describe("30 8 * * SAT,SUN") == "At 08:30, Sunday and Saturday"


def test_dow_full_week_is_star():
    assert describe("0 0 * * 0-6") == "At 00:00 every day"


# --- day-of-month and month -----------------------------------------------------

def test_dom_single_with_month():
    assert describe("0 0 1 1 *") == "At 00:00 on day 1 of the month in January"


def test_dom_range():
    assert describe("0 5 1-7 * *") == "At 05:00 on days 1 through 7 of the month"


def test_dom_list():
    assert describe("0 5 1,15 * *") == "At 05:00 on days 1 and 15 of the month"


def test_dom_list_expands_step_like_run():
    assert describe("0 0 1,3,5 * *") == "At 00:00 on days 1, 3 and 5 of the month"


def test_month_list():
    assert describe("0 0 * 3,6,9 *") == "At 00:00 in March, June and September"


def test_month_range():
    assert describe("0 0 * 1-3 *") == "At 00:00 in January through March"


# --- the day-of-month / day-of-week OR quirk -------------------------------------

def test_dom_and_dow_are_ored():
    assert describe("0 9 1 * 1") == "At 09:00 on day 1 of the month or on Monday"


# --- input hygiene -----------------------------------------------------------------

def test_whitespace_is_forgiving():
    assert describe("  */5   *\t*  * * ") == "Every 5 minutes"


def test_output_is_deterministic():
    assert describe("0 9 * * MON-FRI") == describe("0 9 * * MON-FRI")


# --- error cases ---------------------------------------------------------------------

def test_error_empty_expression():
    with pytest.raises(DescribeError, match="expected 5 space-separated fields"):
        describe("")


def test_error_too_few_fields():
    with pytest.raises(DescribeError, match="got 4"):
        describe("*/5 * * *")


def test_error_too_many_fields():
    with pytest.raises(DescribeError, match="got 6"):
        describe("* * * * * *")


def test_error_bad_token():
    with pytest.raises(DescribeError, match="invalid token 'banana'"):
        describe("banana * * * *")


def test_error_zero_step():
    with pytest.raises(DescribeError, match="step must be at least 1"):
        describe("*/0 * * * *")


def test_error_non_integer_step():
    with pytest.raises(DescribeError, match="step must be an integer"):
        describe("*/x * * * *")


def test_error_step_syntax_on_single_value():
    with pytest.raises(DescribeError, match="step syntax requires"):
        describe("5/2 * * * *")


def test_error_minute_out_of_range():
    with pytest.raises(DescribeError, match="out of range 0-59"):
        describe("60 * * * *")


def test_error_hour_out_of_range():
    with pytest.raises(DescribeError, match="out of range 0-23"):
        describe("0 24 * * *")


def test_error_dom_zero():
    with pytest.raises(DescribeError, match="out of range 1-31"):
        describe("0 0 0 * *")


def test_error_month_out_of_range():
    with pytest.raises(DescribeError, match="out of range 1-12"):
        describe("0 0 1 13 *")


def test_error_dow_out_of_range():
    with pytest.raises(DescribeError, match="out of range 0-7"):
        describe("0 0 * * 8")


def test_error_reversed_range():
    with pytest.raises(DescribeError, match="greater than end"):
        describe("50-10 * * * *")


def test_error_month_names_not_supported_yet():
    with pytest.raises(DescribeError, match="issue #3"):
        describe("0 0 1 JAN *")


def test_error_macros_not_supported_yet():
    with pytest.raises(DescribeError, match="issue #2"):
        describe("@daily")


def test_dom_step_every_other_day():
    assert describe("0 0 */2 * *") == (
        "At 00:00 on days 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29 and 31 of the month")


def test_dom_partial_step():
    assert describe("0 12 1-10/2 * *") == "At 12:00 on days 1, 3, 5, 7 and 9 of the month"


def test_dow_step():
    assert describe("0 9 * * */2") == "At 09:00, Sunday, Tuesday, Thursday and Saturday"


def test_month_step():
    assert describe("0 0 1 */3 *") == (
        "At 00:00 on day 1 of the month in January, April, July and October")


def test_error_dow_full_name():
    with pytest.raises(DescribeError, match="invalid token 'MONDAY'"):
        describe("MONDAY * * * *")


# --- CLI --------------------------------------------------------------------------------

def test_cli_single_quoted_expression(capsys):
    from cronlish.cli import main

    assert main(["*/5 * * * *"]) == 0
    assert capsys.readouterr().out == "Every 5 minutes\n"


def test_cli_unquoted_expression(capsys):
    from cronlish.cli import main

    assert main(["*/5", "*", "*", "*", "*"]) == 0
    assert capsys.readouterr().out == "Every 5 minutes\n"


def test_cli_error_exit_code(capsys):
    from cronlish.cli import main

    assert main(["90 * * * *"]) == 2
    assert "error:" in capsys.readouterr().err
