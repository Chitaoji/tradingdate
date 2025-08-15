"""
Defines date: TradingDate, etc.

NOTE: this module is private. All functions and objects are available in the main
`tradingdate` namespace - use that instead.

"""

from typing import TYPE_CHECKING, Callable, Iterator, Self

if TYPE_CHECKING:
    from .calendar import (
        DayCalendar,
        MonthCalendar,
        TradingCalendar,
        WeekCalendar,
        YearCalendar,
    )

__all__ = ["TradingDate", "split_date", "raise_unexpexted_type"]


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
        self, year: int, month: int, day: int, /, calendar: "TradingCalendar"
    ) -> None:
        self.__date = (year, month, day)
        self.calendar = calendar

    def __eq__(self, value: "Self | int | str | TradingCalendar", /) -> bool:
        if not isinstance(value, (self.__class__, int, str)):
            return value == self
        return self.asint() == int(value)

    def __gt__(self, value: "Self | int | str | TradingCalendar", /) -> bool:
        if not isinstance(value, (self.__class__, int, str)):
            return value < self
        return self.asint() > int(value)

    def __lt__(self, value: "Self | int | str | TradingCalendar", /) -> bool:
        if not isinstance(value, (self.__class__, int, str)):
            return value > self
        return self.asint() < int(value)

    def __ge__(self, value: "Self | int | str | TradingCalendar", /) -> bool:
        if not isinstance(value, (self.__class__, int, str)):
            return value <= self
        return self.asint() >= int(value)

    def __le__(self, value: "Self | int | str | TradingCalendar", /) -> bool:
        if not isinstance(value, (self.__class__, int, str)):
            return value >= self
        return self.asint() <= int(value)

    def __add__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self - abs(value)
        y, m, d = split_date(self.asstr())
        month = self.calendar.cache[y][m]
        idx = month.index(d)
        if idx + value < len(month):
            d = month[idx + value]
            return self.__class__(y, m, d, calendar=self.calendar)
        value -= len(month) - idx
        return self.calendar.get_nearest_date_after(f"{y}{m + 1:02}01") + value

    def __sub__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self + abs(value)
        y, m, d = split_date(self.asstr())
        month = self.calendar.cache[y][m]
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
        y, m, d = self.__date
        return self.calendar.get_nearest_date_after(f"{y}{m:02}{d + 1:02}")

    def last(self) -> Self:
        """Returns the last date."""
        y, m, d = self.__date
        return self.calendar.get_nearest_date_before(f"{y}{m:02}{d - 1:02}")

    def iterate_until(
        self,
        stop: "TradingDate | int | str",
        step: int = 1,
        /,
        *,
        inclusive: bool = False,
    ) -> "DateRange":
        """
        Returns an iterator of trade dates from `self` (inclusive) to
        `stop` (inclusive or exclusive, determined by argument) by `step`.

        Equivalent to `daterange(self, stop, step)` if `inclusive` is
        False.

        Parameters
        ----------
        end : TradingDate | int | str
            End date.
        step : int, optional
            Step, by default 1.
        inclusive : bool, optional
            Determines whether `stop` is inclusive in the iterator.

        Returns
        -------
        DateRange
            Iterator of trade dates.

        """
        return DateRange(self, stop, step, inclusive=inclusive)

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
    def year(self) -> "YearCalendar":
        """Calendar of the year."""
        return self.calendar.get_year(self.__date[0])

    @property
    def month(self) -> "MonthCalendar":
        """Calendar of the month."""
        y, m, _ = self.__date
        return self.calendar.get_month(y, m)

    @property
    def week(self) -> "WeekCalendar":
        """Calendar of the week."""
        return self.calendar.get_week(*self.__date)

    @property
    def day(self) -> "DayCalendar":
        """Calendar of the day."""
        return self.calendar.get_day(*self.__date)


class DateRange:
    """
    Returns an iterator of trade dates from `start` (inclusive) to
    `stop` (inclusive or exclusive, determined by argument) by `step`.

    """

    def __init__(
        self,
        start: TradingDate,
        stop: "TradingDate | int | str",
        step: int = 1,
        /,
        *,
        inclusive: bool = False,
    ) -> None:
        self.__start = start
        self.__stop = stop
        self.__step = step
        self.__inclusive = inclusive

    def __repr__(self) -> str:
        rstr = f"{self.__class__.__name__}({self.__start}, {self.__stop}"
        if self.__step != 1:
            rstr += f", {self.__step}"
        if self.__inclusive:
            rstr += ", inclusive=True"
        rstr += ")"
        return rstr

    def __iter__(self) -> Iterator[TradingDate]:
        if self.__inclusive:
            return self.__iter_inclusively()
        return self.__iter_exclusively()

    def __iter_exclusively(self) -> Iterator[TradingDate]:
        date, stop, step = self.__start, self.__stop, self.__step
        if step == 1:
            while date < stop:
                yield date
                date = date.next()
        elif step == -1:
            while date > stop:
                yield date
                date = date.last()
        elif step == 0:
            raise ValueError("step must not be zero")
        elif step > 0:
            while date < stop:
                yield date
                date = date + step
        else:
            while date > stop:
                yield date
                date = date + step

    def __iter_inclusively(self) -> Iterator[TradingDate]:
        date, stop, step = self.__start, self.__stop, self.__step
        if step == 1:
            while date <= stop:
                yield date
                date = date.next()
        elif step == -1:
            while date >= stop:
                yield date
                date = date.last()
        elif step == 0:
            raise ValueError("step must not be zero")
        elif step > 0:
            while date <= stop:
                yield date
                date = date + step
        else:
            while date >= stop:
                yield date
                date = date + step

    def tolist(self) -> list[TradingDate]:
        """Equivalent to `list(self)`."""
        return list(self)

    def find_every_year(self) -> list["YearCalendar"]:
        """
        Return a list of YearCalendar between `start` (inclusive) and `stop`
        (exclusive) by `step`.

        """
        return sorted(set(x.year for x in self))

    def find_every_month(self) -> list["MonthCalendar"]:
        """
        Return a list of MonthCalendar between `start` (inclusive) and `stop`
        (exclusive) by `step`.

        """
        return sorted(set(x.month for x in self))

    def find_every_week(self) -> list["WeekCalendar"]:
        """
        Return a list of WeekCalendar between `start` (inclusive) and `stop`
        (exclusive) by `step`.

        """
        return sorted(set(x.week for x in self))

    def apply[T](self, func: Callable[[TradingDate], T]) -> list[T]:
        """Apply a function on each TradingDate and return a list."""
        return [func(x) for x in self]


def split_date(date: TradingDate | int | str) -> tuple[int, int, int]:
    """Split date to int numbers: year, month, and day."""
    datestr = str(date)
    return int(datestr[:-4]), int(datestr[-4:-2]), int(datestr[-2:])


def raise_unexpexted_type(typ: type, value: object) -> None:
    """Raise TypeError."""
    raise TypeError(f"expected {typ.__name__}, got {type(value).__name__} instead")
