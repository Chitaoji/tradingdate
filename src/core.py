"""
Contains the core of tradingdate: get_trading_date(), get_calendar(), etc.

NOTE: this module is private. All functions and objects are available in the main
`tradingdate` namespace - use that instead.

"""

from typing import TYPE_CHECKING, Iterator, Literal, Self

import numpy as np

from .calendar_engine import CalendarEngine

if TYPE_CHECKING:
    from ._typing import CalendarDict


__all__ = [
    "get_trading_date",
    "get_trading_dates",
    "get_calendar",
    "TradingDate",
    "TradingCalendar",
]


def get_trading_date(
    date: int | str,
    /,
    calendar_id: str = "chinese",
    missing: Literal["use_next", "use_last", "raise"] = "use_last",
) -> "TradingDate":
    """
    Returns a `TradingDate` object.

    Parameters
    ----------
    date : int | str
        The date.
    calendar_id : str, optional
        Calendar id, by default "chinese".
    missing : Literal["use_next", "use_last", "raise"], optional
        Used when `date` is not found in the calendar. If "use_next",
        return the nearest trade date after `date`; if "use_last",
        return the nearest trade date before it; if "raise", raise
        error. By default "use_last".

    Returns
    -------
    TradingDate
        Trade date.

    """

    calendar = get_calendar(calendar_id)
    match missing:
        case "use_next":
            return calendar.get_nearest_date_after(date)
        case "use_last":
            return calendar.get_nearest_date_before(date)
        case "raise":
            raise NotOnCalendarError(f"date {date} is not on the calendar")
        case _ as x:
            raise ValueError(f"invalid value for argument 'not_exist': {x!r}")


def get_trading_dates(
    start: int | str | None = None,
    end: int | str | None = None,
    calendar_id: str = "chinese",
) -> Iterator["TradingDate"]:
    """
    Returns an iterator of trade dates between `start` and `end`
    (including `start` and `end`).

    Parameters
    ----------
    start : int | str | None, optional
        Start date, by default None.
    end : int | str | None, optional
        End date, by default None.
    calendar_id : str, optional
        Calendar id, by default "chinese".

    Returns
    -------
    Iterator[TradingDate]
        Iterator of trade dates.

    """
    calendar = get_calendar(calendar_id)
    start = calendar.start.asint() if start is None else int(start)
    end = calendar.end.asint() if end is None else int(end)
    return (x for x in calendar if start <= x.asint() <= end)


def get_calendar(calendar_id: str = "chinese", /) -> "TradingCalendar":
    """
    Returns a `TradingCalendar` object.

    Parameters
    ----------
    calendar_id : str, optional
        Calendar id, by default "chinese".

    Returns
    -------
    TradingCalendar
        Calendar.

    """
    match calendar_id:
        case "chinese":
            cal = CalendarEngine().get_chinese_calendar()
        case _ as x:
            raise ValueError(f"invalid calendar_id: {x}")
    return TradingCalendar(cal)


# ==============================================================================
#                                Core Types
# ==============================================================================


class TradingCalendar:
    """
    Stores a trading calendar.

    Parameters
    ----------
    caldict : CalendarDict
        Calendar dict formatted by `{yyyy: {mm: [dd, ...]}}`, with values
        sorted. Empty lists are not allowed.

    """

    __slots__ = ["caldict"]

    def __init__(self, caldict: "CalendarDict", /) -> None:
        if not caldict:
            raise ValueError("empty calendar")
        self.caldict = caldict

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.start} ~ {self.end})"

    def __contains__(self, value: "TradingDate | int | str") -> bool:
        y, m, d = split_date(value)
        return y in self.caldict and m in self.caldict[y] and d in self.caldict[y][m]

    def __iter__(self) -> Iterator["TradingDate"]:
        return (
            TradingDate(y, m, d, calendar=self)
            for y in self.caldict
            for m in self.caldict[y]
            for d in self.caldict[y][m]
        )

    @property
    def start(self) -> "TradingDate":
        """Return the starting date of the calendar."""
        y = min(self.caldict)
        m = min(self.caldict[y])
        d = self.caldict[y][m][0]
        return TradingDate(y, m, d, calendar=self)

    @property
    def end(self) -> "TradingDate":
        """Return the ending date of the calendar."""
        y = max(self.caldict)
        m = max(self.caldict[y])
        d = self.caldict[y][m][-1]
        return TradingDate(y, m, d, calendar=self)

    def get_nearest_date_after(self, date: int | str) -> "TradingDate":
        """Get the nearest date after the date (including itself)."""
        y, m, d = split_date(date)
        if y in self.caldict:
            year = self.caldict[y]
            if m in year:
                month = year[m]
                if d in month:
                    return TradingDate(y, m, d, calendar=self)
                if d <= month[-1]:
                    new_d = month[np.argmax(np.array(month) >= d)]
                    return TradingDate(y, m, new_d, calendar=self)
            if m >= 12:
                return self.get_nearest_date_after(f"{y + 1}0101")
            return self.get_nearest_date_after(f"{y}{m + 1:02}01")
        if y < max(self.caldict):
            return self.get_nearest_date_after(f"{y + 1}0101")
        raise OutOfCalendarError(
            f"date {date} is out of range [{self.start}, {self.end}]"
        )

    def get_nearest_date_before(self, date: int | str) -> "TradingDate":
        """Get the nearest date before the date (including itself)."""
        y, m, d = split_date(date)
        if y in self.caldict:
            year = self.caldict[y]
            if m in year:
                month = year[m]
                if d in month:
                    return TradingDate(y, m, d, calendar=self)
                if d >= month[0]:
                    new_d = month[np.argmin(np.array(month) <= d) - 1]
                    return TradingDate(y, m, new_d, calendar=self)
            if m <= 1:
                return self.get_nearest_date_before(f"{y - 1}1231")
            return self.get_nearest_date_before(f"{y}{m - 1:02}31")
        if y > min(self.caldict):
            return self.get_nearest_date_before(f"{y - 1}1231")
        raise OutOfCalendarError(
            f"date {date} is out of range [{self.start}, {self.end}]"
        )

    def get_year(self, year: int | str) -> "YearCalendar":
        """Returns a year calendar."""
        y = int(year)
        return YearCalendar({y: self.caldict[y]})


class YearCalendar(TradingCalendar):
    """Trading year."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.asint()})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        return self.asint()

    def asint(self) -> int:
        """
        Return the year as an integer number equals to `yyyy`.

        Returns
        -------
        int
            An integer representing the year.

        """
        return list(self.caldict)[0]

    def asstr(self) -> str:
        """
        Return the year as a string formatted by `yyyy`.

        Returns
        -------
        str
            A string representing the year.

        """
        return str(self.asint())

    def get_month(self, month: int | str) -> "MonthCalendar":
        """Returns a month calendar."""
        y = self.asint()
        m = int(month)
        return MonthCalendar({y: {m: self.caldict[y][m]}})


class MonthCalendar(TradingCalendar):
    """Trading month."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self.caldict)[0]}{self.asint():02})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        return self.asint()

    def asint(self) -> int:
        """
        Return an integer number equals to `mm`.

        Returns
        -------
        int
            An integer representing the month.

        """
        return list(list(self.caldict.values())[0])[0]

    def asstr(self) -> str:
        """
        Return a string formatted by `mm`.

        Returns
        -------
        str
            A string representing the month.

        """
        return f"{self.asint():02}"

    def get_day(self, day: int | str) -> "DayCalendar":
        """Returns a day calendar."""
        y = list(self.caldict)[0]
        m = self.asint()
        d = int(day)
        if d not in self.caldict[y][m]:
            raise KeyError(d)
        return DayCalendar({y: {m: [d]}})


class DayCalendar(TradingCalendar):
    """Trading day."""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({list(self.caldict)[0]}"
            f"{list(list(self.caldict.values())[0])[0]:02}{self.asint():02})"
        )

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        return self.asint()

    def asint(self) -> int:
        """
        Return an integer number equals to `dd`.

        Returns
        -------
        int
            An integer representing the day.

        """
        return list(list(self.caldict.values())[0].values())[0][0]

    def asstr(self) -> str:
        """
        Return a string formatted by `dd`.

        Returns
        -------
        str
            A string representing the day.

        """
        return f"{self.asint():02}"


class TradingDate:
    """
    Represents a trade date on a specified trading calendar.

    Parameters
    ----------
    year : int
        Year number.
    month : int
        Month number.
    day : int
        Day number.
    calendar : TradingCalendar
        Specifies the trading calendar.

    """

    __slots__ = ["calendar", "__date"]

    def __init__(
        self, year: int, month: int, day: int, /, calendar: TradingCalendar
    ) -> None:
        self.__date = (year, month, day)
        self.calendar = calendar

    def __eq__(self, value: Self | int | str, /) -> bool:
        return self.asint() == int(value)

    def __gt__(self, value: Self | int | str, /) -> bool:
        return self.asint() > int(value)

    def __lt__(self, value: Self | int | str, /) -> bool:
        return self.asint() < int(value)

    def __ge__(self, value: Self | int | str, /) -> bool:
        return self.asint() >= int(value)

    def __le__(self, value: Self | int | str, /) -> bool:
        return self.asint() <= int(value)

    def __add__(self, value: int, /) -> Self:
        y, m, d = split_date(self.asstr())
        month = self.calendar.caldict[y][m]
        idx = month.index(d)
        if idx + value < len(month):
            d = month[idx + value]
            return self.__class__(y, m, d, calendar=self.calendar)
        value -= len(month) - idx
        return self.calendar.get_nearest_date_after(f"{y}{m + 1:02}01") + value

    def __sub__(self, value: int, /) -> Self:
        y, m, d = split_date(self.asstr())
        month = self.calendar.caldict[y][m]
        idx = month.index(d)
        if idx >= value:
            d = month[idx - value]
            return self.__class__(y, m, d, calendar=self.calendar)
        value -= idx + 1
        return self.calendar.get_nearest_date_before(f"{y}{m - 1:02}31") - value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.asstr()})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        return self.asint()

    def next(self) -> Self:
        """Returns the next date."""
        return self + 1

    def last(self) -> Self:
        """Returns the last date."""
        return self - 1

    def asint(self) -> int:
        """
        Return an integer number equals to `yyyymmdd`.

        Returns
        -------
        int
            An integer representing the date.

        """
        return int(self.asstr())

    def asstr(self) -> str:
        """
        Return a string formatted by `yyyymmdd`.

        Returns
        -------
        str
            A string representing the date.

        """
        y, m, d = self.__date
        return f"{y}{m:02}{d:02}"

    @property
    def year(self) -> YearCalendar:
        """Returns the year."""
        y = self.__date[0]
        return YearCalendar({y: self.calendar.caldict[y]})

    @property
    def month(self) -> MonthCalendar:
        """Returns the month."""
        y, m, _ = self.__date
        return MonthCalendar({y: {m: self.calendar.caldict[y][m]}})

    @property
    def day(self) -> DayCalendar:
        """Returns the day."""
        y, m, d = self.__date
        return DayCalendar({y: {m: [d]}})


def split_date(date: TradingDate | int | str) -> tuple[int, int, int]:
    """Split date to int numbers: year, month, and day."""
    datestr = str(date)
    return int(datestr[:4]), int(datestr[4:6]), int(datestr[6:])


class NotOnCalendarError(Exception):
    """Raised when date is not on the calendar."""


class OutOfCalendarError(Exception):
    """Raised when date is out of the calendar."""
