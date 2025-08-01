from typing import Dict, List

class FDPrecision:
	def __init__(self, index, label):
		self.index = index
		self.name = label
	
	def __repr__(self):
		return f"_DatePrecision(index={self.index}, name={self.capitalize()})"
	
	def __str__(self):
		return self.name.capitalize()
	
	def __int__(self):
		return self.index
	
	def __lt__(self, other):
		if isinstance(other, FDPrecision):
			return self.index < other.index
		raise TypeError(f"Cannot compare DTPrecision with {type(other)}")
	
	def __le__(self, other):
		if isinstance(other, FDPrecision):
			return self.index <= other.index
		raise TypeError(f"Cannot compare DTPrecision with {type(other)}")
	
	Year: 'FDPrecision'
	Month: 'FDPrecision'
	Day: 'FDPrecision'
	Hour: 'FDPrecision'
	Minute: 'FDPrecision'
	Second: 'FDPrecision'
	
	Items: Dict[str, 'FDPrecision']
	DatetimeOrder: List['FDPrecision']
	DateOrder: List['FDPrecision']

FDPrecision.Year = FDPrecision(0, 'year')
FDPrecision.Month = FDPrecision(1, 'month')
FDPrecision.Day = FDPrecision(2, 'day')
FDPrecision.Hour = FDPrecision(3, 'hour')
FDPrecision.Minute = FDPrecision(4, 'minute')
FDPrecision.Second = FDPrecision(5, 'second')

FDPrecision.DatetimeOrder = [
	FDPrecision.Year,
	FDPrecision.Month,
	FDPrecision.Day,
	FDPrecision.Hour,
	FDPrecision.Minute,
	FDPrecision.Second,
]

FDPrecision.DateOrder = [
	FDPrecision.Year,
	FDPrecision.Month,
	FDPrecision.Day,
]

FDPrecision.Items = {
	p.name: p
	for p in FDPrecision.DatetimeOrder
}
