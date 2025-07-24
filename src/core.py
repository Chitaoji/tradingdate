"""
Contains the core of tradedate: ... , etc.

NOTE: this module is private. All functions and objects are available in the main
`tradedate` namespace - use that instead.

"""

from typing import Literal, Self

import numpy as np

__all__ = ["tradedate", "TradeDate", "TradingCalendar"]


def tradedate(
    date: int | str,
    calendar_id: str = "chinese",
    not_exist: Literal["forward", "backward"] = "backward",
):
    """
    Returns a `TradeDate` object.

    Returns
    -------
    date : int | str
        The date.
    calendar_id : str, optional
        Calendar id, by default "chinese".
    not_exist : Literal["forward", "backward"], optional
        Used when `date` is not found in the calendar. If "forward", return
        the nearest trade date after `date`; if "backward", return the nearest
        trade date before it. By default "backward".

    """
    match calendar_id:
        case "chinese":
            calendar = TradingCalendar([20240101])
        case _ as x:
            raise ValueError(f"invalid calendar_id: {x}")
    match not_exist:
        case "forward":
            return calendar.get_nearest_date_after(date)
        case "backward":
            return calendar.get_nearest_date_before(date)
        case _ as x:
            raise ValueError(f"invalid fix_date: {x}")


class TradingCalendar:
    """
    Stores a trading calendar.

    Parameters
    ----------
    dates : list[int | str]
        List of dates.

    """

    __slots__ = ["dates", "__start_date", "__end_date"]

    def __init__(self, dates: list[int | str]) -> None:
        if not dates:
            raise ValueError("empty dates")
        self.dates = [int(d) for d in dates]
        self.__start_date = min(self.dates)
        self.__end_date = max(self.dates)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__start_date} ~ {self.__end_date})"

    def __contains__(self, value: "TradeDate | int | str") -> bool:
        return int(value) in self.dates

    @property
    def start(self) -> "TradeDate":
        """Return the starting date of the calendar."""
        return TradeDate(self.__start_date, calendar=self)

    @property
    def end(self) -> "TradeDate":
        """Return the ending date of the calendar."""
        return TradeDate(self.__end_date, calendar=self)

    def get_nearest_date_after(self, date: int | str) -> "TradeDate":
        """Get the nearest date after the date (including itself)."""
        if (date := int(date)) > self.__end_date:
            raise OutOfCalendarError(
                f"date {date} is out of range [{self.__start_date}, {self.__end_date}]"
            )
        new_date = self.dates[np.argmax(np.array(self.dates) >= date)]
        return TradeDate(new_date, calendar=self)

    def get_nearest_date_before(self, date: int | str) -> "TradeDate":
        """Get the nearest date before the date (including itself)."""
        if (date := int(date)) < self.__end_date:
            raise OutOfCalendarError(
                f"date {date} is out of range [{self.__start_date}, {self.__end_date}]"
            )
        new_date = self.dates[np.argmin(np.array(self.dates) <= date) - 1]
        return TradeDate(new_date, calendar=self)


class YearCalendar(TradingCalendar):
    """Trading year."""

    __slots__ = ["__year"]

    def __init__(self, year: int, dates: list[int | str]) -> None:
        super().__init__(dates)
        self.__year = year

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__year})"

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
        return self.__year

    def asstr(self) -> str:
        """
        Return the year as a string formatted by `yyyy`.

        Returns
        -------
        str
            A string representing the year.

        """
        return str(self.__year)


class MonthCalendar(TradingCalendar):
    """Trading month."""

    __slots__ = ["__year", "__month"]

    def __init__(self, year: int, month: int, dates: list[int | str]) -> None:
        super().__init__(dates)
        self.__year = year
        self.__month = month

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__year}{self.__month:02})"

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
        return self.__month

    def asstr(self) -> str:
        """
        Return a string formatted by `mm`.

        Returns
        -------
        str
            A string representing the month.

        """
        return f"{self.__month:02}"


class DayCalendar(TradingCalendar):
    """Trading day."""

    __slots__ = ["__year", "__month", "__day"]

    def __init__(self, year: int, month: int, day: int, dates: list[int | str]) -> None:
        super().__init__(dates)
        self.__year = year
        self.__month = month
        self.__day = day

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.__year}{self.__month:02}{self.__day:02})"
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
        return self.__day

    def asstr(self) -> str:
        """
        Return a string formatted by `dd`.

        Returns
        -------
        str
            A string representing the day.

        """
        return f"{self.__day:02}"


class TradeDate:
    """
    Represents a trade date on a specified trading calendar.

    Parameters
    ----------
    date : int | str
        The date.
    calendar : TradingCalendar
        Specifies the trading calendar.

    """

    __slots__ = ["calendar", "__date"]

    def __init__(self, date: int | str, calendar: TradingCalendar) -> None:
        self.calendar = calendar
        if (date := int(date)) not in self.calendar:
            raise NotOnCalendarError(f"date {date} is not on the calendar")
        self.__date = date

    def __eq__(self, value: Self | int | str, /) -> bool:
        return int(self) == int(value)

    def __add__(self, value: int, /) -> Self:
        dates = self.calendar.dates
        new_idx = dates.index(self.__date) + value
        if new_idx >= len(dates):
            raise OutOfCalendarError(
                f"date {self} + {value} is out of range "
                f"[{self.calendar.start}, {self.calendar.end}]"
            )
        return self.__class__(dates[new_idx], calendar=self.calendar)

    def __sub__(self, value: int, /) -> Self:
        dates = self.calendar.dates
        new_idx = dates.index(self.__date) - value
        if new_idx < 0:
            raise OutOfCalendarError(
                f"date {self} - {value} is out of range "
                f"[{self.calendar.start}, {self.calendar.end}]"
            )
        return self.__class__(dates[new_idx], calendar=self.calendar)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__date})"

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
        return self.__date

    def asstr(self) -> str:
        """
        Return a string formatted by `yyyymmdd`.

        Returns
        -------
        str
            A string representing the date.

        """
        return str(self.__date)

    @property
    def year(self) -> YearCalendar:
        """Returns the year."""
        y = self.asstr()[:4]
        return YearCalendar(int(y), [x for x in self.calendar.dates if str(x)[:4] == y])

    @property
    def month(self) -> MonthCalendar:
        """Returns the month."""
        m = self.asstr()[:6]
        return MonthCalendar(
            int(m[:4]), int(m[4:]), [x for x in self.calendar.dates if str(x)[:6] == m]
        )

    @property
    def day(self) -> DayCalendar:
        """Returns the day."""
        d = self.asstr()
        return DayCalendar(int(d[:4]), int(d[4:6]), int(d[6:]), [self.asint()])


class NotOnCalendarError(Exception):
    """Raised when date is not on the calendar."""


class OutOfCalendarError(Exception):
    """Raised when date is out of the calendar."""
