"""True Solar Time (TST) correction, per PRD section 7.2.

``lunar-python`` consumes the wall-clock time exactly as given and performs no
astronomical or geographical correction (verified against its source). Chinese
divination therefore requires TST to be applied *before* constructing
``Solar(...)``; otherwise users far from the 120E standard meridian receive a
shifted hour/day pillar.

Formula (PRD 7.2):
    local_mean_time = standard_time + (longitude - standard_meridian) * 4 min
    true_solar_time = local_mean_time + E(t)
where E(t) is the equation of time (apparent minus mean solar time).
"""

from datetime import datetime, timedelta
from math import cos, pi, sin

# Standard meridian of China Standard Time (Beijing), degrees east.
STANDARD_MERIDIAN_CN = 120.0
# Each degree of longitude corresponds to four minutes of solar time.
MINUTES_PER_DEGREE = 4.0


def equation_of_time_minutes(moment: datetime) -> float:
    """Return the equation of time E(t) in minutes for a civil datetime.

    Uses the NOAA / Spencer analytical approximation of the equation of time,
    accurate to well under a minute across the year. Positive values mean the
    apparent sun is ahead of the mean sun.
    """
    day_of_year = moment.timetuple().tm_yday
    hour_fraction = moment.hour + moment.minute / 60.0 + moment.second / 3600.0
    gamma = 2 * pi / 365.0 * (day_of_year - 1 + (hour_fraction - 12) / 24.0)
    return 229.18 * (
        0.000075
        + 0.001868 * cos(gamma)
        - 0.032077 * sin(gamma)
        - 0.014615 * cos(2 * gamma)
        - 0.040849 * sin(2 * gamma)
    )


def longitude_offset_minutes(longitude: float, standard_meridian: float = STANDARD_MERIDIAN_CN) -> float:
    """Return the local-mean-time offset in minutes for a longitude."""
    return (longitude - standard_meridian) * MINUTES_PER_DEGREE


def true_solar_time(
    standard_dt: datetime,
    longitude: float,
    standard_meridian: float = STANDARD_MERIDIAN_CN,
) -> datetime:
    """Convert a standard-time (e.g. Beijing) datetime to True Solar Time.

    Day-boundary crossings are handled naturally by timedelta arithmetic, so a
    correction that pushes the moment past midnight yields the correct
    previous/next civil day for pillar derivation.
    """
    offset = longitude_offset_minutes(longitude, standard_meridian)
    offset += equation_of_time_minutes(standard_dt)
    return standard_dt + timedelta(minutes=offset)


def true_solar_offset_minutes(
    standard_dt: datetime,
    longitude: float,
    standard_meridian: float = STANDARD_MERIDIAN_CN,
) -> float:
    """Return the total TST correction in minutes (TST minus standard time)."""
    return longitude_offset_minutes(longitude, standard_meridian) + equation_of_time_minutes(standard_dt)
