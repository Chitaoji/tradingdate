"""
Contains the core of tradingdate: get_trading_date(), get_calendar(), etc.

NOTE: this module is private. All functions and objects are available in the main
`tradingdate` namespace - use that instead.

"""

from typing import Iterator, Literal

from .calendar import NotOnCalendarError, TradingCalendar
from .calendar_engine import CalendarEngine
from .date import DateRange, TradingDate

__all__ = [
    "get_trading_date",
    "get_trading_dates",
    "daterange",
    "get_calendar",
    "make_calendar",
]


def get_trading_date(
    date: int | str,
    /,
    calendar_id: str = "chinese",
    missing: Literal["use_next", "use_last", "raise"] = "use_last",
) -> TradingDate:
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
) -> Iterator[TradingDate]:
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
    start: TradingDate, stop: TradingDate | int | str, step: int = 1, /
) -> DateRange:
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


def get_calendar(calendar_id: str = "chinese") -> TradingCalendar:
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


def make_calendar(calendar_id: str, date_list: list[int | str]) -> TradingCalendar:
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
