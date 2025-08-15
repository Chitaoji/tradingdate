# tradingdate
Manages trade dates.

## Installation
```sh
$ pip install tradingdate
```

## Requirements
```txt
chinesecalendar
```
## Usage
### Get a calendar
```py
>>> import tradingdate as td
>>> cal = td.get_calendar("chinese") # by default "chinese"
>>> cal
TradingCalendar(20040102 ~ 20251231, 'chinese')
>>> list(cal)[:3]
[TradingDate(20040102), TradingDate(20040105), TradingDate(20040106)]
```

### Get a trading date
```py
>>> date = td.get_trading_date(20250116)
>>> date
TradingDate(20250116)
>>> print(date.year, date.month, date.day)
2025 01 16

>>> date - 20
TradingDate(20241218)
>>> date + 100
TradingDate(20250617)

>>> date.week.start, date.week.end
(TradingDate(20250113), TradingDate(20250117))
>>> date.month.start, date.month.end
(TradingDate(20250102), TradingDate(20250127))
>>> date.year.start, date.year.end
(TradingDate(20250102), TradingDate(20251231))
```

### Get iterator of trading dates
```py
>>> list(td.get_trading_dates(20250101, 20250106))
[TradingDate(20250102), TradingDate(20250103), TradingDate(20250106)]
```

### Make a new calendar
```py
>>> td.make_calendar("user-defined", [20250101, 20250115, 20250201])
TradingCalendar(20250101 ~ 20250201, 'user-defined')
>>> list(td.get_trading_dates(20250101, 20250131, calendar_id="user-defined"))
[TradingDate(20250101), TradingDate(20250115)]
```

## See Also
### Github repository
* https://github.com/Chitaoji/tradingdate/

### PyPI project
* https://pypi.org/project/tradingdate/

## License
This project falls under the BSD 3-Clause License.

## History
### v0.0.9
* Updated support for comparison operators and 'in' operators.

### v0.0.8
* Bugfix: no longer raises an OutOfCalendarError when the `end` parameter for `get_trading_dates()` is None. 
* New method `TradingDate.iterate_until()`.
* `daterange()` returns an instance of `DateRange` now.

### v0.0.7
* Updated `make_calendar()`: raises ValueError when `calender_id` already exists.

### v0.0.6
* New function `daterange()`.

### v0.0.5
* New property `TradingDate.week`.

### v0.0.4
* Improved effeciency when making a calendar.
* Updated message of NotImplementedError raised by `CalendarEngine.get_chinese_calendar()`.

### v0.0.3
* Updated `make_calendar()`: now accepts a date-list as the second positional argument instead of a dict.

### v0.0.2
* New function `make_calendar()`.
* Removed the dependency on `numpy`.

### v0.0.1
* New methods `TradingCalendar.get_year()`, `YearCalendar.get_month()`, `MonthCalendar.get_day()`.
* Bugfix: `TradingDate.__sub__()`.

### v0.0.0
* Initial release.