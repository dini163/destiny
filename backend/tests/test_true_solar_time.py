"""Unit tests for True Solar Time correction (``app.solar.true_solar_time``)."""

from datetime import date, datetime, timedelta

import pytest

from app.solar.true_solar_time import (
    STANDARD_MERIDIAN_CN,
    equation_of_time_minutes,
    longitude_offset_minutes,
    true_solar_offset_minutes,
    true_solar_time,
)

# Real reference longitudes reused across cases.
URUMQI_LON = 87.6168
BEIJING_LON = 116.4074
CHENGDU_LON = 104.0668
TOKYO_LON = 139.6503


def test_longitude_offset_is_zero_at_standard_meridian() -> None:
    assert longitude_offset_minutes(STANDARD_MERIDIAN_CN) == 0.0


@pytest.mark.parametrize(
    ("longitude", "expected_minutes"),
    [(104.1, -63.6), (90.0, -120.0), (BEIJING_LON, -14.3704), (TOKYO_LON, 78.6012)],
)
def test_longitude_offset_is_four_minutes_per_degree(longitude: float, expected_minutes: float) -> None:
    assert longitude_offset_minutes(longitude) == pytest.approx(expected_minutes, abs=1e-3)


def test_equation_of_time_stays_within_physical_bounds() -> None:
    """Apparent-minus-mean solar time never exceeds roughly -15 / +17 minutes."""
    start = datetime(2024, 1, 1, 12, 0)
    for day in range(366):
        eot = equation_of_time_minutes(start + timedelta(days=day))
        assert -16.0 <= eot <= 17.0


def test_equation_of_time_reaches_known_annual_extrema() -> None:
    # Minimum near 11 February, maximum near 3 November (NOAA reference).
    assert equation_of_time_minutes(datetime(2024, 2, 11, 12)) < -12.0
    assert equation_of_time_minutes(datetime(2024, 11, 3, 12)) > 14.0


def test_at_standard_meridian_offset_equals_equation_of_time() -> None:
    moment = datetime(1988, 2, 15, 23, 30)
    assert true_solar_offset_minutes(moment, STANDARD_MERIDIAN_CN) == pytest.approx(
        equation_of_time_minutes(moment)
    )


def test_offset_is_self_consistent_with_returned_datetime() -> None:
    moment = datetime(2000, 6, 21, 8, 15)
    corrected = true_solar_time(moment, CHENGDU_LON)
    delta_minutes = (corrected - moment).total_seconds() / 60.0
    assert delta_minutes == pytest.approx(true_solar_offset_minutes(moment, CHENGDU_LON))


def test_far_west_location_rolls_back_across_midnight() -> None:
    # 00:10 Beijing time in Urumqi is still the previous solar day.
    corrected = true_solar_time(datetime(2024, 1, 1, 0, 10), URUMQI_LON)
    assert corrected.date() == date(2023, 12, 31)
    assert corrected.hour == 21


def test_west_of_meridian_yields_earlier_solar_time() -> None:
    moment = datetime(2024, 3, 20, 12, 0)
    assert true_solar_time(moment, URUMQI_LON) < moment


def test_east_of_meridian_yields_later_solar_time() -> None:
    moment = datetime(2024, 3, 20, 12, 0)
    assert true_solar_time(moment, TOKYO_LON) > moment
