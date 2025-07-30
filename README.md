# tradingdate
Manages trade dates.

## Installation
```sh
$ pip install tradingdate
```

## Requirements
```txt
chinesecalendar
numpy
```
## Usage
### Get the calendar
```py
>>> import tradingdate as td
>>> cal = td.get_calendar("chinese") # by default "chinese"
>>> cal
TradingCalendar(20040102 ~ 20251231)
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
>>> date.month.start, date.month.end
(TradingDate(20250102), TradingDate(20250127))
>>> date.year.start, date.year.end
(TradingDate(20250102), TradingDate(20251231))
```

### Get trading dates
```py
>>> list(td.get_trading_dates(20250101, 20250106))
[TradingDate(20250102), TradingDate(20250103), TradingDate(20250106)]
```


## See Also
### Github repository
* https://github.com/Chitaoji/tradingdate/

### PyPI project
* https://pypi.org/project/tradingdate/

## License
This project falls under the BSD 3-Clause License.

## History
### v0.0.2
* Removed the dependency on `numpy`.

### v0.0.1
* New methods `TradingCalendar.get_year()`, `YearCalendar.get_month()`, `MonthCalendar.get_day()`.
* Bugfix: `TradingDate.__sub__()`.

### v0.0.0
* Initial release.