"""
Contains the core of tradedate: ... , etc.

NOTE: this module is private. All functions and objects are available in the main
`tradedate` namespace - use that instead.

"""

from typing import *

import numpy as np

DateLike = Union["TradeDate", int, str]

__all__ = ["TradeDate", "DateLike"]


class TradeDate:
    """
    Represents a trade date on a specified trading calender.

    Parameters
    ----------
    date : DateLike
        The trade date. If the date is not found in the calender, use
        the next date after it.
    calender : str, optional
        Specifies the trading calender, by default "chinese".

    """

    def __init__(self, date: DateLike, calender: str = "chinese"):
        if calender is None:
            if isinstance(date, self.__class__):
                self.calender = date.calender
                self._date = date._date
                self._on_calender = date._on_calender
                return
            else:
                self.calender = self._find_calender()
        else:
            self.calender = sorted([int(x) for x in calender])
        _min = min(self.calender)
        _max = max(self.calender)

        _tmp_date = int(date)
        if _tmp_date < _min:
            # warnings.warn(
            #     f"{_tmp_date} is out of range ({_min}:{_max}).",
            #     DateRangeWarning,
            #     stacklevel=2,
            # )
            _tmp_date = _min
        if _tmp_date > _max:
            # warnings.warn(
            #     f"{_tmp_date} is out of range ({_min}:{_max}).",
            #     DateRangeWarning,
            #     stacklevel=2,
            # )
            _tmp_date = _max

        self._date = _tmp_date

        if self._date in self.calender:
            self._on_calender = True
        else:
            self._on_calender = False

    def _find_calender(self) -> List[int]:
        raise CalenderError("calender is not specified")

    def __eq__(self, __value: DateLike) -> bool:
        return int(self) == int(__value)

    def __add__(self, __value: int) -> "TradeDate":
        if not self._on_calender:
            raise NotOnCalenderError(
                f"{self._date} is not in the calender, use .next() or .last() to \
jump to the nearest calendar date"
            )
        date = self.calender[self.calender.index(self._date) + __value]
        return self.__class__(date, calender=self.calender)

    def __sub__(self, __value: int) -> "TradeDate":
        if not self._on_calender:
            raise NotOnCalenderError(
                f"{self._date} is not in the calender, use .next() or .last() to \
jump to the nearest calendar date"
            )
        date = self.calender[self.calender.index(self._date) - __value]
        return self.__class__(date, calender=self.calender)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._date})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        return self.asint()

    def next(self) -> "TradeDate":
        """
        If the current date is not present in the calender, jump to the nearest
        calnder date after it, or nothing will happen.

        Returns
        -------
        CalenderDate
            A new instance.

        """
        date = self.calender[np.argmax(np.array(self.calender) >= self._date)]
        return self.__class__(date, calender=self.calender)

    def last(self) -> "TradeDate":
        """
        If the current date is not present in the calender, jump to the nearest
        calnder date before it, or nothing will happen.

        Returns
        -------
        CalenderDate
            A new instance.

        """
        date = self.calender[np.argmin(np.array(self.calender) <= self._date) - 1]
        return self.__class__(date, calender=self.calender)

    def asint(self) -> int:
        """
        Return the date as an integer number equals to `yyyymmdd`.

        Returns
        -------
        int
            An integer representing the date.

        """
        return self._date

    def asstr(self) -> str:
        """
        Return the date as a string formatted as `yyyymmdd`.

        Returns
        -------
        str
            A string representing the date.

        """
        return str(self._date)

    @property
    def year(self) -> int:
        return int(self.asstr()[:4])

    @property
    def month(self) -> int:
        return int(self.asstr()[4:6])

    @property
    def day(self) -> int:
        return int(self.asstr()[6:])


class CalenderError(Exception):
    pass


class NotOnCalenderError(CalenderError):
    pass


class DateRangeWarning(Warning):
    pass
