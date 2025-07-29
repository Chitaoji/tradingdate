"""
Contains the core of tradedate: tradedate(), get_calendar(), etc.

NOTE: this module is private. All functions and objects are available in the main
`tradedate` namespace - use that instead.

"""

from typing import TYPE_CHECKING, Iterator, Literal, Self

import numpy as np

from .calendar_engine import CalendarEngine

if TYPE_CHECKING:
    from ._typing import CalendarDict


__all__ = [
    "tradedate",
    "get_tradedates",
    "get_calendar",
    "TradeDate",
    "TradingCalendar",
]


def tradedate(
    date: int | str,
    /,
    calendar_id: str = "chinese",
    not_exist: Literal["forward", "backward"] = "backward",
) -> "TradeDate":
    """
    Returns a `TradeDate` object.

    Parameters
    ----------
    date : int | str
        The date.
    calendar_id : str, optional
        Calendar id, by default "chinese".
    not_exist : Literal["forward", "backward"], optional
        Used when `date` is not found in the calendar. If "forward", return
        the nearest trade date after `date`; if "backward", return the nearest
        trade date before it. By default "backward".

    Returns
    -------
    TradeDate
        Trade date.

    """

    calendar = get_calendar(calendar_id)
    match not_exist:
        case "forward":
            return calendar.get_nearest_date_after(date)
        case "backward":
            return calendar.get_nearest_date_before(date)
        case _ as x:
            raise ValueError(f"invalid value for argument 'not_exist': {x!r}")


def get_tradedates(
    start: int | str | None = None,
    end: int | str | None = None,
    calendar_id: str = "chinese",
) -> Iterator["TradeDate"]:
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
    Iterator[TradeDate]
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
        Calendar dict formatted by `{yyyy: {mm: [dd, ...]}}`, must be
        sorted.

    """

    __slots__ = ["caldict"]

    def __init__(self, caldict: "CalendarDict", /) -> None:
        if not caldict:
            raise ValueError("empty calendar")
        self.caldict = caldict

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.start} ~ {self.end})"

    def __contains__(self, value: "TradeDate | int | str") -> bool:
        y, m, d = split_date(value)
        return y in self.caldict and m in self.caldict[y] and d in self.caldict[y][m]

    def __iter__(self) -> Iterator["TradeDate"]:
        return (
            TradeDate(y, m, d, calendar=self)
            for y in self.caldict
            for m in self.caldict[y]
            for d in self.caldict[y][m]
        )

    @property
    def start(self) -> "TradeDate":
        """Return the starting date of the calendar."""
        y = min(self.caldict)
        m = min(self.caldict[y])
        d = self.caldict[y][m][0]
        return TradeDate(y, m, d, calendar=self)

    @property
    def end(self) -> "TradeDate":
        """Return the ending date of the calendar."""
        y = max(self.caldict)
        m = max(self.caldict[y])
        d = self.caldict[y][m][-1]
        return TradeDate(y, m, d, calendar=self)

    def get_nearest_date_after(self, date: int | str) -> "TradeDate":
        """Get the nearest date after the date (including itself)."""
        y, m, d = split_date(date)
        if y in self.caldict:
            month = self.caldict[y][m]
            if d in month:
                return TradeDate(y, m, d, calendar=self)
            if d <= month[-1]:
                new_d = month[np.argmax(np.array(month) >= d)]
                return TradeDate(y, m, new_d, calendar=self)
            if m < 12:
                return self.get_nearest_date_after(f"{y}{m + 1:02}01")
            return self.get_nearest_date_after(f"{y + 1}0101")
        raise OutOfCalendarError(
            f"date {date} is out of range [{self.start}, {self.end}]"
        )

    def get_nearest_date_before(self, date: int | str) -> "TradeDate":
        """Get the nearest date before the date (including itself)."""
        y, m, d = split_date(date)
        if y in self.caldict:
            month = self.caldict[y][m]
            if d in month:
                return TradeDate(y, m, d, calendar=self)
            if d >= month[0]:
                new_d = month[np.argmin(np.array(month) <= d) - 1]
                return TradeDate(y, m, new_d, calendar=self)
            if m > 1:
                return self.get_nearest_date_before(f"{y}{m - 1:02}31")
            return self.get_nearest_date_before(f"{y - 1}1231")
        raise OutOfCalendarError(
            f"date {date} is out of range [{self.start}, {self.end}]"
        )


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


class TradeDate:
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
        year = self.calendar.caldict[y]
        month = year[m]
        idx = month.index(d)
        if idx + value < len(month):
            d = month[idx + value]
            return self.__class__(y, m, d, calendar=self.calendar)
        value -= len(month) - idx
        if m + 1 in year:
            d = year[m + 1][0]
            return self.__class__(y, m + 1, d, calendar=self.calendar) + value
        if y + 1 in self.calendar.caldict:
            year = self.calendar.caldict[y + 1]
            m = min(year)
            d = year[m][0]
            return self.__class__(y + 1, m, d, calendar=self.calendar) + value
        raise OutOfCalendarError(
            f"result is out of range " f"[{self.calendar.start}, {self.calendar.end}]"
        )

    def __sub__(self, value: int, /) -> Self:
        y, m, d = split_date(self.asstr())
        year = self.calendar.caldict[y]
        month = year[m]
        idx = month.index(d)
        if idx - value >= 0:
            d = month[idx - value]
            return self.__class__(y, m, d, calendar=self.calendar)
        value -= idx + 1
        if m - 1 in year:
            d = year[m - 1][-1]
            return self.__class__(y, m - 1, d, calendar=self.calendar) - value
        if y - 1 in self.calendar.caldict:
            year = self.calendar.caldict[y - 1]
            m = max(year)
            d = year[m][-1]
            return self.__class__(y - 1, m, d, calendar=self.calendar) - value
        raise OutOfCalendarError(
            f"result is out of range [{self.calendar.start}, {self.calendar.end}]"
        )

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


def split_date(date: TradeDate | int | str) -> tuple[int, int, int]:
    """Split date to int numbers: year, month, and day."""
    datestr = str(date)
    return int(datestr[:4]), int(datestr[4:6]), int(datestr[6:])


class OutOfCalendarError(Exception):
    """Raised when date is out of the calendar."""
