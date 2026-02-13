"""
Contains the core of tradingdate: get_trading_date(), get_calendar(), etc.

NOTE: this module is private. All functions and objects are available in the main
`tradingdate` namespace - use that instead.

"""

from typing import Iterator, Literal

from .calendar import NotOnCalendarError, TradingCalendar
from .calendar_engine import CalendarEngine
from .date import DateRange, TradingDate

__all__ = ["date", "daterange", "get_calendar", "make_calendar"]


def date(
    date: int | str,
    /,
    calendar_id: str = "chinese",
    missing: Literal["use_next", "use_before", "raise"] = "use_before",
) -> TradingDate:
    """
    Returns a `TradingDate` object.

    Parameters
    ----------
    date : int | str
        The date.
    calendar_id : str, optional
        Calendar id, by default "chinese".
    missing : Literal["use_next", "use_before", "raise"], optional
        Used when `date` is not found in the calendar. If "use_next",
        return the nearest trade date after `date`; if "use_before",
        return the nearest trade date before it; if "raise", raise
        error. By default "use_before".

    Returns
    -------
    TradingDate
        Trade date.

    """

    calendar = get_calendar(calendar_id)
    match missing:
        case "use_next":
            return calendar.get_nearest_date_after(date)
        case "use_before":
            return calendar.get_nearest_date_before(date)
        case "raise":
            raise NotOnCalendarError(f"date {date} is not on the calendar")
        case _ as x:
            raise ValueError(f"invalid value for argument 'not_exist': {x!r}")


def daterange(
    start: int | str | None = None,
    end: int | str | None = None,
    step: int = 1,
    /,
    calendar_id: str = "chinese",
    include_end: bool = False,
) -> DateRange:
    """
    Returns an iterator of trade dates from `start` (inclusive) to
    `stop` (exclusive) by `step`.

    Parameters
    ----------
    start : int | str | None, optional
        Start date, by default None.
    end : int | str | None, optional
        End date, by default None.
    step : int, optional
        Step, by default 1.
    calendar_id : str, optional
        Calendar id, by default "chinese".
    include_end : bool, optional
        Whether the end date should be included, by default False.

    Returns
    -------
    DateRange
        Iterator of trade dates.

    """
    calendar = get_calendar(calendar_id)
    date = calendar.start if start is None else calendar.get_nearest_date_after(start)
    end = calendar.end if end is None else end
    return DateRange(date, end, step, include_end=include_end)


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


def make_calendar(
    calendar_id: str, dates: Iterator[int | str | TradingDate]
) -> TradingCalendar:
    """
    Make a new calendar and register it in the engine.

    Parameters
    ----------
    calendar_id : str
        Calendar id.
    dates : Iterator[int | str | TradingDate]
        Dates formatted by `yyyymmdd`.

    Returns
    -------
    TradingCalendar
        Calendar.

    """
    engine = CalendarEngine()
    engine.register_calendar(TradingCalendar, calendar_id, list(dates))
    return engine.get_calendar(calendar_id)
