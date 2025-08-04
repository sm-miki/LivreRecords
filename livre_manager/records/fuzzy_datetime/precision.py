"""
fuzzy_datetime.precision
日時の精度を表すクラスを定義する。
"""
from typing import Dict, List

class DatetimePrecision:
	def __init__(self, index, label):
		self.index = index
		self.name = label
	
	def __repr__(self):
		return f"DatetimePrecision.{self.name.capitalize()}"
	
	def __str__(self):
		return self.name
	
	def __int__(self):
		return self.index
	
	def __lt__(self, other):
		if isinstance(other, DatetimePrecision):
			return self.index < other.index
		raise TypeError(f"Cannot compare DTPrecision with {type(other)}")
	
	def __le__(self, other):
		if isinstance(other, DatetimePrecision):
			return self.index <= other.index
		raise TypeError(f"Cannot compare DTPrecision with {type(other)}")
	
	Year: 'DatetimePrecision'
	Month: 'DatetimePrecision'
	Day: 'DatetimePrecision'
	Hour: 'DatetimePrecision'
	Minute: 'DatetimePrecision'
	Second: 'DatetimePrecision'
	
	Items: Dict[str, 'DatetimePrecision']
	DatetimeOrder: List['DatetimePrecision']
	DateOrder: List['DatetimePrecision']

DatetimePrecision.Year = DatetimePrecision(0, 'year')
DatetimePrecision.Month = DatetimePrecision(1, 'month')
DatetimePrecision.Day = DatetimePrecision(2, 'day')
DatetimePrecision.Hour = DatetimePrecision(3, 'hour')
DatetimePrecision.Minute = DatetimePrecision(4, 'minute')
DatetimePrecision.Second = DatetimePrecision(5, 'second')

DatetimePrecision.DatetimeOrder = [
	DatetimePrecision.Year,
	DatetimePrecision.Month,
	DatetimePrecision.Day,
	DatetimePrecision.Hour,
	DatetimePrecision.Minute,
	DatetimePrecision.Second,
]

DatetimePrecision.DateOrder = [
	DatetimePrecision.Year,
	DatetimePrecision.Month,
	DatetimePrecision.Day,
]

DatetimePrecision.Items = {
	p.name: p
	for p in DatetimePrecision.DatetimeOrder
}
