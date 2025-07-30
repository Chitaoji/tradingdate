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
        self.__calendar_cache[calendar_id] = caldict

    def get_calendar(self, calendar_id: str) -> "CalendarDict":
        """Get a calendar."""
        return self.__calendar_cache[calendar_id]
