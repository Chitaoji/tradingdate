"""
Contains the core of tradedate: ... , etc.

NOTE: this module is private. All functions and objects are available in the main
`tradedate` namespace - use that instead.

"""

from typing import Literal, Self

import numpy as np

__all__ = ["tradedate", "TradeDate", "TradingCalender"]


def tradedate(
    date: int | str,
    calender_id: str = "chinese",
    not_exist: Literal["forward", "backward"] = "backward",
):
    """
    Returns a `TradeDate` object.

    Returns
    -------
    date : int | str
        The date.
    calender_id : str, optional
        Calender id, by default "chinese".
    not_exist : Literal["forward", "backward"], optional
        If "forward", use the next trade date instead of `date` when `date`
        is not found in the calender; if "backward", use the last trade date.
        By default "backward".

    """
    match calender_id:
        case "chinese":
            calender = TradingCalender([20240101])
        case _ as x:
            raise ValueError(f"invalid calender_id: {x}")
    match not_exist:
        case "forward":
            return calender.get_nearest_date_after(date)
        case "backward":
            return calender.get_nearest_date_before(date)
        case _ as x:
            raise ValueError(f"invalid fix_date: {x}")


class TradingCalender:
    """
    Stores a trading calender.

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
        """Return the starting date of the calender."""
        return TradeDate(self.__start_date, calender=self)

    @property
    def end(self) -> "TradeDate":
        """Return the ending date of the calender."""
        return TradeDate(self.__end_date, calender=self)

    def get_nearest_date_after(self, date: int | str) -> "TradeDate":
        """Get the nearest date after the date (including itself)."""
        if (date := int(date)) > self.__end_date:
            raise OutOfCalenderError(
                f"date {date} is out of range [{self.__start_date}, {self.__end_date}]"
            )
        new_date = self.dates[np.argmax(np.array(self.dates) >= date)]
        return TradeDate(new_date, calender=self)

    def get_nearest_date_before(self, date: int | str) -> "TradeDate":
        """Get the nearest date before the date (including itself)."""
        if (date := int(date)) < self.__end_date:
            raise OutOfCalenderError(
                f"date {date} is out of range [{self.__start_date}, {self.__end_date}]"
            )
        new_date = self.dates[np.argmin(np.array(self.dates) <= date) - 1]
        return TradeDate(new_date, calender=self)


class TradingPeriod(TradingCalender):
    """Trading period."""

    __slots__ = ["__name"]

    def __init__(self, name: str, dates: list[int | str]) -> None:
        super().__init__(dates)
        self.__name = name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__name})"

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
        return int(self.__name)

    def asstr(self) -> str:
        """
        Return the year as a string formatted by `yyyy`.

        Returns
        -------
        str
            A string representing the year.

        """
        return self.__name


class TradingYear(TradingPeriod):
    """Trading year."""


class TradingMonth(TradingPeriod):
    """Trading month."""


class TradingDay(TradingPeriod):
    """Trading day."""


class TradeDate:
    """
    Represents a trade date on a specified trading calender.

    Parameters
    ----------
    date : int | str
        The date.
    calender : TradingCalender
        Specifies the trading calender.

    """

    __slots__ = ["calender", "__date"]

    def __init__(self, date: int | str, calender: TradingCalender) -> None:
        self.calender = calender
        if (date := int(date)) not in self.calender:
            raise NotOnCalenderError(f"date {date} is not on the calender")
        self.__date = date

    def __eq__(self, value: Self | int | str, /) -> bool:
        return int(self) == int(value)

    def __add__(self, value: int, /) -> Self:
        dates = self.calender.dates
        new_idx = dates.index(self.__date) + value
        if new_idx >= len(dates):
            raise OutOfCalenderError(
                f"date {self} + {value} is out of range "
                f"[{self.calender.start}, {self.calender.end}]"
            )
        return self.__class__(dates[new_idx], calender=self.calender)

    def __sub__(self, value: int, /) -> Self:
        dates = self.calender.dates
        new_idx = dates.index(self.__date) - value
        if new_idx < 0:
            raise OutOfCalenderError(
                f"date {self} - {value} is out of range "
                f"[{self.calender.start}, {self.calender.end}]"
            )
        return self.__class__(dates[new_idx], calender=self.calender)

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
        Return the date as an integer number equals to `yyyymmdd`.

        Returns
        -------
        int
            An integer representing the date.

        """
        return self.__date

    def asstr(self) -> str:
        """
        Return the date as a string formatted by `yyyymmdd`.

        Returns
        -------
        str
            A string representing the date.

        """
        return str(self.__date)

    @property
    def year(self) -> TradingYear:
        """Returns the year."""
        return int(self.asstr()[:4])

    @property
    def month(self) -> TradingMonth:
        """Returns the month."""
        return TradingMonth(self.asstr()[4:6], [])

    @property
    def day(self) -> int:
        """Returns the day."""
        return TradingDay(self.asstr()[6:], [self.asint()])


class NotOnCalenderError(Exception):
    """Raised when date is not on the calender."""


class OutOfCalenderError(Exception):
    """Raised when date is out of the calender."""
