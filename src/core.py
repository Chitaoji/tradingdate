"""
Contains the core of tradedate: ... , etc.

NOTE: this module is private. All functions and objects are available in the main
`tradedate` namespace - use that instead.

"""

from typing import Literal, Self

import numpy as np

__all__ = ["TradeDate", "TradingCalender"]


def tradedate(
    date: int | str,
    calender_id: str = "chinese",
    fix_date: Literal["forward", "backward"] = "backward",
):
    """
    Returns a `TradeDate` object.

    Returns
    -------
    date : int | str
        The date.
    calender_id : str, optional
        Calender id, by default "chinese".
    fix_date : Literal["forward", "backward"], optional
        If "forward", use the next trade date instead of `date` when `date`
        is not found in the calender; if "backward", use the last trade date.
        By default "backward".

    """
    match calender_id:
        case "chinese":
            calender = TradingCalender([])
        case _ as x:
            raise ValueError(f"invalid calender_id: {x}")
    match fix_date:
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

    def __init__(self, dates: list[int | str], calender_id: int | None = None) -> None:
        if not dates:
            raise ValueError("empty dates")
        self.dates = [int(d) for d in dates]
        self.__start_date = min(self.dates)
        self.__end_date = max(self.dates)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__start_date} ~ {self.__end_date})"

    def start(self) -> "TradeDate":
        """Return the staring date of the calender."""
        return TradeDate(self.__start_date, calender=self)

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


class TradingYear(TradingCalender):
    """Trading year."""

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


class TradingMonth(TradingCalender):
    """Trading month."""

    def __init__(self, month: int, dates: list[int | str]) -> None:
        super().__init__(dates)
        self.__month = month

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__month})"

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
        return self.__month

    def asstr(self) -> str:
        """
        Return the year as a string formatted by `yyyy`.

        Returns
        -------
        str
            A string representing the year.

        """
        return str(self.__month)


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

    def __init__(self, date: int | str, calender: TradingCalender) -> None:
        self.calender = calender
        if (date := int(date)) not in self.calender:
            raise NotOnCalenderError(f"date {date} is not on the calender")
        self.__date = date

    def __eq__(self, value: Self | int | str, /) -> bool:
        return int(self) == int(value)

    def __add__(self, value: int, /) -> Self:
        dates = self.calender.dates
        new_date = dates[dates.index(self.__date) + value]
        return self.__class__(new_date, calender=self.calender)

    def __sub__(self, value: int, /) -> Self:
        dates = self.calender.dates
        new_date = dates[max(0, dates.index(self.__date) - value)]
        return self.__class__(new_date, calender=self.calender)

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
    def year(self) -> int:
        return int(self.asstr()[:4])

    @property
    def month(self) -> int:
        return int(self.asstr()[4:6])

    @property
    def day(self) -> int:
        return int(self.asstr()[6:])


class NotOnCalenderError(Exception):
    """Raised when date is not on the calender."""


class OutOfCalenderError(Exception):
    """Raised when date is out of the calender."""
