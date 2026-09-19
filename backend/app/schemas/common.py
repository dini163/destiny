"""Shared Pydantic schemas used across divination systems."""

from datetime import date, time
from enum import Enum

from pydantic import BaseModel, Field


class CalendarType(str, Enum):
    """Calendar system of the supplied birth date."""

    SOLAR = "solar"
    LUNAR = "lunar"


class Gender(str, Enum):
    """Subject gender; required by systems whose luck pillars depend on it."""

    MALE = "male"
    FEMALE = "female"


class BirthInput(BaseModel):
    """Common birth-data input shared by natal-chart systems."""

    birth_date: date = Field(description="Birth date in the selected calendar.")
    birth_time: time = Field(description="Birth time, precise to the minute.")
    calendar: CalendarType = Field(default=CalendarType.SOLAR)
    city: str | None = Field(default=None, description="City name for geocoding.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    gender: Gender | None = Field(default=None)


class TrueSolarTimeResponse(BaseModel):
    """True Solar Time preview shown in the input console."""

    standard_time: str
    true_solar_time: str
    offset_minutes: float
    longitude: float
