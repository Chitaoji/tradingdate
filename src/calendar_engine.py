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
            try:
                workdays = chinese_calendar.get_workdays(
                    datetime.date(y, m, d),
                    datetime.date(datetime.datetime.now().year, 12, 31),
                )
            except NotImplementedError as e:
                e.add_note(
                    "please try 'pip install --upgrade chinesecalendar' in the "
                    "console"
                )
                raise e
            for x in workdays:
                if x.year == y:
                    if x.month == m:
                        d = x.day
                        cal[y][m].append(d)
                    else:
                        m, d = x.month, x.day
                        cal[y][m] = [d]
                else:
                    y, m, d = x.year, x.month, x.day
                    cal[y] = {}
                    cal[y][m] = [d]
            self.__calendar_cache["chinese"] = cal
        return self.__calendar_cache["chinese"]

    def register_calendar(self, calendar_id: str, date_list: list[int | str]) -> None:
        """Register a calendar."""
        datestr_list: list[str] = sorted({str(x) for x in date_list})
        y, m, d = -1, -1, -1
        cal: "CalendarDict" = {}
        for datestr in datestr_list:
            if len(datestr) <= 4:
                raise ValueError(f"invalid date: {datestr}")
            yy, mm, dd = int(datestr[:-4]), int(datestr[-4:-2]), int(datestr[-2:])
            if yy == y:
                if mm == m:
                    self.__check_day(d := dd)
                    cal[y][m].append(d)
                else:
                    self.__check_month(m := mm)
                    self.__check_day(d := dd)
                    cal[y][m] = [d]
            else:
                self.__check_year(y := yy)
                self.__check_month(m := mm)
                self.__check_day(d := dd)
                cal[y] = {}
                cal[y][m] = [d]
        self.__calendar_cache[calendar_id] = cal

    def get_calendar(self, calendar_id: str) -> "CalendarDict":
        """Get a calendar."""
        return self.__calendar_cache[calendar_id]

    def __check_year(self, year: int) -> None:
        if year < 0:
            raise ValueError(f"invalid year number: {year}")

    def __check_month(self, month: int) -> None:
        if not 1 <= month <= 12:
            raise ValueError(f"invalid month number: {month}")

    def __check_day(self, day: int) -> None:
        if not 1 <= day <= 31:
            raise ValueError(f"invalid day number: {day}")
