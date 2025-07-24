"""
Provides the tool for getting calendars: CalendarEngine.

NOTE: this module is private. All functions and objects are available in the main
`tradedate` namespace - use that instead.

"""

import datetime

import chinese_calendar

__all__ = ["CalendarEngine"]


class CalendarEngine:
    """Calendar engine."""

    calendar_cache: dict[str, list[int]] = {}

    def get_chinese_calendar(self) -> list[int]:
        """Get the chinese calendar."""
        if "chinese" not in self.__class__.calendar_cache:
            self.__class__.calendar_cache["chinese"] = [
                int(x.strftime("%Y%m%d"))
                for x in chinese_calendar.get_workdays(
                    datetime.date(2004, 1, 1), datetime.date(2025, 1, 1)
                )
            ]
        return self.__class__.calendar_cache["chinese"]
