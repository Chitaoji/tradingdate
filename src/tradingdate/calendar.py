"""
Defines calendar: TradingCalendar, etc.

NOTE: this module is private. All functions and objects are available in the main
`tradingdate` namespace - use that instead.

"""

import datetime
import sys
from typing import TYPE_CHECKING, Iterator, Self

from .calendar_engine import CalendarEngine
from .date import TradingDate, raise_unexpexted_type, split_date

if TYPE_CHECKING:
    from ._typing import CalendarDict

__all__ = [
    "TradingCalendar",
    "YearCalendar",
    "MonthCalendar",
    "WeekCalendar",
    "DayCalendar",
    "NotOnCalendarError",
    "OutOfCalendarError",
]


class TradingCalendar:
    """
    Stores a trading calendar.

    Parameters
    ----------
    cache : CalendarDict
        Calendar dict formatted by `{yyyy: {mm: [dd, ...]}}`, with values
        sorted. Empty lists are not allowed.

    """

    __slots__ = ["id", "cache"]

    def __init__(self, calendar_id: str, cache: "CalendarDict", /) -> None:
        if not cache:
            raise ValueError("empty calendar")
        self.id = calendar_id
        self.cache = cache

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.start} ~ {self.end}, {self.id!r})"

    def __contains__(
        self, value: "int | str | TradingDate | TradingCalendar", /
    ) -> bool:
        if isinstance(value, (int, str, TradingDate)):
            y, m, d = split_date(value)
            return y in self.cache and m in self.cache[y] and d in self.cache[y][m]
        if isinstance(value, TradingCalendar):
            return value.id == self.id
        return False

    def __iter__(self) -> Iterator["TradingDate"]:
        return (
            TradingDate(y, m, d, calendar=self.origin())
            for y in self.cache
            for m in self.cache[y]
            for d in self.cache[y][m]
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def __valur2str(self, value: "int | str | TradingDate | TradingCalendar", /) -> str:
        if value.__class__ is TradingCalendar or self.__class__ is TradingCalendar:
            raise_unsupported_operator(self, value, 2)
        if isinstance(value, int):
            value = str(value)
        elif isinstance(value, (TradingCalendar, TradingDate)):
            value = str(hash(value))
        elif not isinstance(value, str):
            raise_unsupported_operator(self, value, 2)
        return value

    def __eq__(self, value: "int | str | TradingDate | TradingCalendar", /) -> bool:
        if value.__class__ is TradingCalendar and self.__class__ is TradingCalendar:
            return self.id == value.id
        return str(hash(self)) == self.__valur2str(value)

    def __gt__(self, value: "int | str | TradingDate | TradingCalendar", /) -> bool:
        return str(hash(self)) > self.__valur2str(value)

    def __lt__(self, value: "int | str | TradingDate | TradingCalendar", /) -> bool:
        return str(hash(self)) < self.__valur2str(value)

    def __ge__(self, value: "int | str | TradingDate | TradingCalendar", /) -> bool:
        return str(hash(self)) >= self.__valur2str(value)

    def __le__(self, value: "int | str | TradingDate | TradingCalendar", /) -> bool:
        return str(hash(self)) <= self.__valur2str(value)

    @property
    def start(self) -> "TradingDate":
        """Return the starting date of the calendar."""
        y = min(self.cache)
        m = min(self.cache[y])
        d = self.cache[y][m][0]
        return TradingDate(y, m, d, calendar=self.origin())

    @property
    def end(self) -> "TradingDate":
        """Return the ending date of the calendar."""
        y = max(self.cache)
        m = max(self.cache[y])
        d = self.cache[y][m][-1]
        return TradingDate(y, m, d, calendar=self.origin())

    def get_nearest_date_after(self, date: int | str) -> "TradingDate":
        """Get the nearest date after the date (including itself)."""
        y, m, d = split_date(date)
        if y in self.cache:
            ydict = self.cache[y]
            if m in ydict:
                mlist = ydict[m]
                if d in mlist:
                    return TradingDate(y, m, d, calendar=self.origin())
                if d <= mlist[-1]:
                    for dd in mlist:
                        if dd >= d:
                            return TradingDate(y, m, dd, calendar=self.origin())
                    raise RuntimeError("unexpected runtime behavior")
            if m >= 12:
                return self.get_nearest_date_after(f"{y + 1}0101")
            return self.get_nearest_date_after(f"{y}{m + 1:02}01")
        if y < max(self.cache):
            return self.get_nearest_date_after(f"{y + 1}0101")
        raise OutOfCalendarError(
            f"date {date} is out of range [{self.start}, {self.end}]"
        )

    def get_nearest_date_before(self, date: int | str) -> "TradingDate":
        """Get the nearest date before the date (including itself)."""
        y, m, d = split_date(date)
        if y in self.cache:
            ydict = self.cache[y]
            if m in ydict:
                mlist = ydict[m]
                if d in mlist:
                    return TradingDate(y, m, d, calendar=self.origin())
                if d >= mlist[0]:
                    for dd in reversed(mlist):
                        if dd <= d:
                            return TradingDate(y, m, dd, calendar=self.origin())
                    raise RuntimeError("unexpected runtime behavior")
            if m <= 1:
                return self.get_nearest_date_before(f"{y - 1}1231")
            return self.get_nearest_date_before(f"{y}{m - 1:02}31")
        if y > min(self.cache):
            return self.get_nearest_date_before(f"{y - 1}1231")
        raise OutOfCalendarError(
            f"date {date} is out of range [{self.start}, {self.end}]"
        )

    def get_year(self, year: int | str) -> "YearCalendar":
        """Returns a year calendar."""
        y = int(year)
        return YearCalendar(self.id, {y: self.origin().cache[y]})

    def get_month(self, year: int | str, month: int | str) -> "MonthCalendar":
        """Returns a month calendar."""
        y, m = int(year), int(month)
        return MonthCalendar(self.id, {y: {m: self.origin().cache[y][m]}})

    def get_day(
        self, year: int | str, month: int | str, day: int | str
    ) -> "DayCalendar":
        """Returns a day calendar."""
        y, m, d = int(year), int(month), int(day)
        return DayCalendar(self.id, {y: {m: [d]}})

    def get_week(
        self, year: int | str, month: int | str, day: int | str
    ) -> "WeekCalendar":
        """Returns a week calendar."""
        y, m, d = int(year), int(month), int(day)
        w = datetime.date(y, m, d).weekday()
        cdict: "CalendarDict" = {}
        cal = self.origin()
        for date in [
            datetime.date(y, m, d) + datetime.timedelta(days=x)
            for x in range(-w, 7 - w)
        ]:
            y, m, d = date.year, date.month, date.day
            if f"{y}{m:02}{d:02}" in cal:
                if y not in cdict:
                    cdict[y] = {}
                if m not in cdict[y]:
                    cdict[y][m] = [d]
                else:
                    cdict[y][m].append(d)
        return WeekCalendar(self.id, cdict)

    def origin(self) -> Self:
        """Return the original calendar."""
        if self.__class__ is TradingCalendar:
            return self
        return CalendarEngine().get_calendar(self.id)


class YearCalendar(TradingCalendar):
    """Trading year."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.asint()}, {self.id!r})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        return self.asint()

    def __add__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self - abs(value)
        cal = self.origin()
        year_list = list(cal.cache)
        idx = year_list.index(self.asint())
        if idx + value < len(year_list):
            y = year_list[idx + value]
            return cal.get_year(y)
        raise OutOfCalendarError(
            f"year {self} + {value} is out of range [{cal.start}, {cal.end}]"
        )

    def __sub__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self + abs(value)
        cal = self.origin()
        year_list = list(cal.cache)
        idx = year_list.index(self.asint())
        if idx >= value:
            y = year_list[idx - value]
            return cal.get_year(y)
        raise OutOfCalendarError(
            f"year {self} - {value} is out of range [{cal.start}, {cal.end}]"
        )

    def __contains__(
        self, value: "int | str | TradingDate | TradingCalendar", /
    ) -> bool:
        if isinstance(value, (int, str, TradingDate)):
            return super().__contains__(value)
        if isinstance(value, TradingCalendar):
            if not value.id == self.id:
                return False
            if isinstance(value, YearCalendar):
                return False
            return str(hash(self)) in str(hash(value))
        return False

    def next(self) -> Self:
        """Return the next year."""
        return self.end.next().year

    def last(self) -> Self:
        """Return the last year."""
        return self.start.last().year

    def asint(self) -> int:
        """
        Return the year as an integer number equals to `yyyy`.

        Returns
        -------
        int
            An integer representing the year.

        """
        return list(self.cache)[0]

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
        return f"{self.__class__.__name__}({hash(self)}, {self.id!r})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        y = list(self.cache)[0]
        return int(f"{y}{self.asint():02}")

    def __add__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self - abs(value)
        cal = self.origin()
        month_list = [int(f"{y}{m:02}") for y, x in cal.cache.items() for m in x]
        idx = month_list.index(hash(self))
        if idx + value < len(month_list):
            y = month_list[idx + value]
            return cal.get_year(str(y)[:4]).get_month(str(y)[4:])
        raise OutOfCalendarError(
            f"month {hash(self)} + {value} is out of range [{cal.start}, {cal.end}]"
        )

    def __sub__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self + abs(value)
        cal = self.origin()
        month_list = [int(f"{y}{m:02}") for y, x in cal.cache.items() for m in x]
        idx = month_list.index(hash(self))
        if idx >= value:
            y = month_list[idx - value]
            return cal.get_year(str(y)[:4]).get_month(str(y)[4:])
        raise OutOfCalendarError(
            f"month {hash(self)} - {value} is out of range [{cal.start}, {cal.end}]"
        )

    def __contains__(
        self, value: "int | str | TradingDate | TradingCalendar", /
    ) -> bool:
        if isinstance(value, (int, str, TradingDate)):
            return super().__contains__(value)
        if isinstance(value, TradingCalendar):
            if not value.id == self.id:
                return False
            if isinstance(value, (YearCalendar, MonthCalendar)):
                return False
            return str(hash(self)) in str(hash(value))
        return False

    def next(self) -> Self:
        """Return the next month."""
        return self.end.next().month

    def last(self) -> Self:
        """Return the last month."""
        return self.start.last().month

    def asint(self) -> int:
        """
        Return an integer number equals to `mm`.

        Returns
        -------
        int
            An integer representing the month.

        """
        return list(list(self.cache.values())[0])[0]

    def asstr(self) -> str:
        """
        Return a string formatted by `mm`.

        Returns
        -------
        str
            A string representing the month.

        """
        return f"{self.asint():02}"


class WeekCalendar(TradingCalendar):
    """Trading week."""

    def __repr__(self) -> str:
        y = list(self.cache)[0]
        return f"{self.__class__.__name__}({y} week{self.asstr()}, {self.id!r})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        return int(f"{hash(self.start) - 1}{self.asstr()}")

    def __add__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self - abs(value)
        week = self
        for _ in range(value):
            week = week.next()
        return week

    def __sub__(self, value: int, /) -> Self:
        if not isinstance(value, int):
            raise_unexpexted_type(int, value)
        if value < 0:
            return self + abs(value)
        week = self
        for _ in range(value):
            week = week.last()
        return week

    def __contains__(
        self, value: "int | str | TradingDate | TradingCalendar", /
    ) -> bool:
        if isinstance(value, (int, str, TradingDate)):
            return super().__contains__(value)
        if isinstance(value, TradingCalendar):
            if not value.id == self.id:
                return False
            if isinstance(value, (YearCalendar, MonthCalendar, WeekCalendar)):
                return False
            return super().__contains__(value.start)
        return False

    def next(self) -> Self:
        """Return the next week."""
        return self.end.next().week

    def last(self) -> Self:
        """Return the last week."""
        return self.start.last().week

    def asint(self) -> int:
        """
        Return an integer number equals to `ww`.

        Returns
        -------
        int
            An integer representing the day.

        """
        return int(self.asstr())

    def asstr(self) -> str:
        """
        Return a string formatted by `ww`.

        Returns
        -------
        str
            A string representing the day.

        """
        return datetime.date(*split_date(self.start)).strftime("%W")


class DayCalendar(TradingCalendar):
    """Trading day."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({hash(self)}, {self.id!r})"

    def __str__(self) -> str:
        return self.asstr()

    def __int__(self) -> int:
        return self.asint()

    def __hash__(self) -> int:
        y = list(self.cache)[0]
        m = list(list(self.cache.values())[0])[0]
        return int(f"{y}{m:02}{self.asint():02}")

    def __add__(self, value: int, /) -> Self:
        return (self.end + value).day

    def __sub__(self, value: int, /) -> Self:
        return (self.start - value).day

    def __contains__(
        self, value: "int | str | TradingDate | TradingCalendar", /
    ) -> bool:
        if isinstance(value, (int, str, TradingDate)):
            return super().__contains__(value)
        return False

    def next(self) -> Self:
        """Return the next day."""
        return self.end.next().day

    def last(self) -> Self:
        """Return the last day."""
        return self.start.last().day

    def asint(self) -> int:
        """
        Return an integer number equals to `dd`.

        Returns
        -------
        int
            An integer representing the day.

        """
        return list(list(self.cache.values())[0].values())[0][0]

    def asstr(self) -> str:
        """
        Return a string formatted by `dd`.

        Returns
        -------
        str
            A string representing the day.

        """
        return f"{self.asint():02}"


def raise_unsupported_operator(obj: object, value: object, stacklevel: int) -> None:
    """Raise TypeError."""
    match sys._getframe(stacklevel).f_code.co_name:  # pylint: disable=protected-access
        case "__eq__":
            op = "=="
        case "__gt__":
            op = ">"
        case "__lt__":
            op = "<"
        case "__ge__":
            op = ">="
        case "__le__":
            op = "<="
        case _ as x:
            op = x
    raise TypeError(
        f"{op!r} not supported between instances of {obj.__class__.__name__!r} "
        f"and {value.__class__.__name__!r}"
    )


class NotOnCalendarError(Exception):
    """Raised when date is not on the calendar."""


class OutOfCalendarError(Exception):
    """Raised when date is out of the calendar."""
