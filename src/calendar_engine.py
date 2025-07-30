"""
Provides the tool for getting calendars: CalendarEngine.

NOTE: this module is private. All functions and objects are available in the main
`tradingdate` namespace - use that instead.

"""

import datetime
from typing import TYPE_CHECKING

import chinese_calendar

if TYPE_CHECKING:
    from ._typing import CalendarDict

__all__ = ["CalendarEngine"]


class CalendarEngine:
    """
    Calendar engine.

    Output should be dicts formatted by `{yyyy: {mm: [dd, ...]}}`. The
    numbers are sorted.

    """

    __calendar_cache: dict[str, "CalendarDict"] = {}

    def get_chinese_calendar(self) -> "CalendarDict":
        """Get the chinese calendar."""
        if "chinese" not in self.__calendar_cache:
            y, m, d = 2004, 1, 1
            cal: "CalendarDict" = {y: {m: []}}
            for x in chinese_calendar.get_workdays(
                datetime.date(y, m, d),
                datetime.date(datetime.datetime.now().year, 12, 31),
            ):
                if x.year == y:
                    if x.month == m:
                        y, m, d = x.year, x.month, x.day
                        cal[y][m].append(d)
                    else:
                        y, m, d = x.year, x.month, x.day
                        cal[y][m] = [d]
                else:
                    y, m, d = x.year, x.month, x.day
                    cal[y] = {}
                    cal[y][m] = [d]
            self.__calendar_cache["chinese"] = cal
        return self.__calendar_cache["chinese"]

    def register_calendar(self, calendar_id: str, caldict: "CalendarDict") -> None:
        """Register a calendar."""
        new_dict: "CalendarDict" = {}
        for y in caldict:
            self.__check_year(y)
            new_ydict: dict[int, list[int]] = {}
            for m in (ydict := caldict[y]):
                self.__check_month(m)
                if mlist := ydict[m]:
                    for d in mlist:
                        self.__check_day(d)
                    new_ydict[m] = sorted(set(mlist))
            if new_ydict:
                new_dict[y] = dict(sorted(new_ydict.items()))
        self.__calendar_cache[calendar_id] = dict(sorted(new_dict.items()))

    def get_calendar(self, calendar_id: str) -> "CalendarDict":
        """Get a calendar."""
        return self.__calendar_cache[calendar_id]

    def __check_year(self, year: int) -> None:
        if not isinstance(year, int):
            raise TypeError(f"expected int, got {type(year).__name__} instead")

    def __check_month(self, month: int) -> None:
        if not isinstance(month, int):
            raise TypeError(f"expected int, got {type(month).__name__} instead")
        if not 1 <= month <= 12:
            raise ValueError(f"invalid month number: {month}")

    def __check_day(self, day: int) -> None:
        if not isinstance(day, int):
            raise TypeError(f"expected int, got {type(day).__name__} instead")
        if not 1 <= day <= 31:
            raise ValueError(f"invalid day number: {day}")
