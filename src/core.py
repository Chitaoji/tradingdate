"""
Contains the core of tradingdate: get_trading_date(), get_calendar(), etc.

NOTE: this module is private. All functions and objects are available in the main
`tradingdate` namespace - use that instead.

"""

import datetime
from typing import TYPE_CHECKING, Iterator, Literal, Self

from .calendar_engine import CalendarEngine

if TYPE_CHECKING:
    from ._typing import CalendarDict


__all__ = [
    "get_trading_date",
    "get_trading_dates",
    "daterange",
    "get_calendar",
    "make_calendar",
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
    if not isinstance(start, (int, str)):
        raise TypeError(f"invalid startdate type: {type(start)}")
    if not isinstance(end, (int, str)):
        raise TypeError(f"invalid enddate type: {type(end)}")
    calendar = get_calendar(calendar_id)
    date = calendar.start if start is None else calendar.get_nearest_date_after(start)
    end = calendar.end.asint() if end is None else int(end)
    while date < end:
        yield date
        date = date.next()
    if date == end:
        yield date


def daterange(
    start: "TradingDate", stop: "TradingDate | int | str", step: int = 1, /
) -> "DateRange":
    """
    Returns an iterator of trade dates from `start` (inclusive) to
    `stop` (exclusive) by `step`.

    Parameters
    ----------
    start : TradingDate
        Start date.
    end : TradingDate | int | str
        End date.
    step : int, optional
        Step, by default 1.

    Returns
    -------
    DateRange
        Iterator of trade dates.

    """
    return DateRange(start, stop, step)


def get_calendar(calendar_id: str = "chinese") -> "TradingCalendar":
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
    engine = CalendarEngine()
    match calendar_id:
        case "chinese":
            cal = engine.get_chinese_calendar(TradingCalendar)
        case _ as x:
            cal = engine.get_calendar(x)
    return cal


def make_calendar(calendar_id: str, date_list: list[int | str]) -> "TradingCalendar":
    """
    Make a new calendar and register it in the engine.

    Parameters
    ----------
    calendar_id : str
        Calendar id.
    date_list : list[int | str]
        List of dates formatted by `yyyymmdd`.

    Returns
    -------
    TradingCalendar
        Calendar.

    """
    engine = CalendarEngine()
    engine.register_calendar(TradingCalendar, calendar_id, date_list)
    return engine.get_calendar(calendar_id)


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

    __slots__ = ["id", "cache"]

    def __init__(self, calendar_id: str, caldict: "CalendarDict", /) -> None:
        if not caldict:
            raise ValueError("empty calendar")
        self.id = calendar_id
        self.cache = caldict

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.start} ~ {self.end}, {self.id!r})"

    def __contains__(self, value: "TradingDate | int | str") -> bool:
        y, m, d = split_date(value)
        return y in self.cache and m in self.cache[y] and d in self.cache[y][m]

    def __iter__(self) -> Iterator["TradingDate"]:
        return (
            TradingDate(y, m, d, calendar=self.origin())
            for y in self.cache
            for m in self.cache[y]
            for d in self.cache[y][m]
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def __valur2str(self, value: Self | int | str | "TradingDate", /) -> str:
        if value.__class__ is TradingCalendar or self.__class__ is TradingCalendar:
            raise_unsupported_operator("==", self, value)
        if isinstance(value, int):
            value = str(value)
        elif isinstance(value, (TradingCalendar, TradingDate)):
            value = str(hash(value))
        elif not isinstance(value, str):
            raise_unsupported_operator("==", self, value)
        return value

    def __eq__(self, value: Self | int | str | "TradingDate", /) -> bool:
        if value.__class__ is TradingCalendar and self.__class__ is TradingCalendar:
            return self.id == value.id
        return str(hash(self)) == self.__valur2str(value)

    def __gt__(self, value: Self | int | str | "TradingDate", /) -> bool:
        return str(hash(self)) > self.__valur2str(value)

    def __lt__(self, value: Self | int | str | "TradingDate", /) -> bool:
        return str(hash(self)) < self.__valur2str(value)

    def __ge__(self, value: Self | int | str | "TradingDate", /) -> bool:
        return str(hash(self)) >= self.__valur2str(value)

    def __le__(self, value: Self | int | str | "TradingDate", /) -> bool:
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
        if self.__class__ is not TradingCalendar:
            raise TypeError(
                f"{self.__class__.__name__!r} object has no method 'get_year()'"
            )
        y = int(year)
        return YearCalendar(self.id, {y: self.cache[y]})

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

    def get_month(self, month: int | str) -> "MonthCalendar":
        """Returns a month calendar."""
        y = self.asint()
        m = int(month)
        return MonthCalendar(self.id, {y: {m: self.cache[y][m]}})


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

    def get_day(self, day: int | str) -> "DayCalendar":
        """Returns a day calendar."""
        y = list(self.cache)[0]
        m = self.asint()
        d = int(day)
        if d not in self.cache[y][m]:
            raise KeyError(d)
        return DayCalendar(self.id, {y: {m: [d]}})


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

    def __eq__(self, value: Self | int | str | TradingCalendar, /) -> bool:
        if isinstance(value, TradingCalendar):
            return value == self
        return self.asint() == int(value)

    def __gt__(self, value: Self | int | str | TradingCalendar, /) -> bool:
        if isinstance(value, TradingCalendar):
            return value < self
        return self.asint() > int(value)

    def __lt__(self, value: Self | int | str | TradingCalendar, /) -> bool:
        if isinstance(value, TradingCalendar):
            return value > self
        return self.asint() < int(value)

    def __ge__(self, value: Self | int | str | TradingCalendar, /) -> bool:
        if isinstance(value, TradingCalendar):
            return value <= self
        return self.asint() >= int(value)

    def __le__(self, value: Self | int | str | TradingCalendar, /) -> bool:
        if isinstance(value, TradingCalendar):
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
    def year(self) -> YearCalendar:
        """Calendar of the year."""
        y = self.__date[0]
        return YearCalendar(self.calendar.id, {y: self.calendar.cache[y]})

    @property
    def month(self) -> MonthCalendar:
        """Calendar of the month."""
        y, m, _ = self.__date
        return MonthCalendar(self.calendar.id, {y: {m: self.calendar.cache[y][m]}})

    @property
    def week(self) -> WeekCalendar:
        """Calendar of the week."""
        w = datetime.date(*self.__date).weekday()
        cal: "CalendarDict" = {}
        for date in [
            datetime.date(*self.__date) + datetime.timedelta(days=x)
            for x in range(-w, 7 - w)
        ]:
            y, m, d = date.year, date.month, date.day
            if f"{y}{m:02}{d:02}" in self.calendar:
                if y not in cal:
                    cal[y] = {}
                if m not in cal[y]:
                    cal[y][m] = [d]
                else:
                    cal[y][m].append(d)
        return WeekCalendar(self.calendar.id, cal)

    @property
    def day(self) -> DayCalendar:
        """Calendar of the day."""
        y, m, d = self.__date
        return DayCalendar(self.calendar.id, {y: {m: [d]}})


def split_date(date: TradingDate | int | str) -> tuple[int, int, int]:
    """Split date to int numbers: year, month, and day."""
    datestr = str(date)
    return int(datestr[:-4]), int(datestr[-4:-2]), int(datestr[-2:])


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

    def find_every_year(self) -> list[YearCalendar]:
        """
        Return a list of every year between `start` (inclusive) and `stop`
        (exclusive) by `step`.

        """
        return sorted(set(x.year for x in self))

    def find_every_month(self) -> list[MonthCalendar]:
        """
        Return a list of every month between `start` (inclusive) and `stop`
        (exclusive) by `step`.

        """
        return sorted(set(x.month for x in self))

    def find_every_week(self) -> list[WeekCalendar]:
        """
        Return a list of every week between `start` (inclusive) and `stop`
        (exclusive) by `step`.

        """
        return sorted(set(x.week for x in self))


def raise_unsupported_operator(op: str, obj: object, value: object) -> None:
    """Raise TypeError."""
    raise TypeError(
        f"{op!r} not supported between instances of {obj.__class__.__name__!r} "
        f"and {value.__class__.__name__!r}"
    )


def raise_unexpexted_type(typ: type, value: object) -> None:
    """Raise TypeError."""
    raise TypeError(f"expected {typ.__name__}, got {type(value).__name__} instead")


class NotOnCalendarError(Exception):
    """Raised when date is not on the calendar."""


class OutOfCalendarError(Exception):
    """Raised when date is out of the calendar."""
