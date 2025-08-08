"""
fuzzy_datetime.precision
日時の精度を表すクラスを定義する。
"""
from typing import Dict, List, Tuple
from enum import IntEnum

class DatePrecision(IntEnum):
	YEAR = 0
	MONTH = 1
	DAY = 2
	HOUR = 3
	MINUTE = 4
	SECOND = 5
	MAX = SECOND
	
	@classmethod
	def all(cls) -> Tuple["DatePrecision", ...]:
		# tuple() で全メンバーを列挙
		return tuple(cls)
	
	@classmethod
	def date_precisions(cls) -> Tuple["DatePrecision", ...]:
		# IntEnum なので <= DAY が効く
		return cls.YEAR, cls.MONTH, cls.DAY
	
	@classmethod
	def slice(cls, start, end, step=1) -> Tuple["DatePrecision", ...]:
		return tuple(cls)[start:end:step]
	
	@classmethod
	def by_name(cls, name: str) -> "DatePrecision":
		"""
		名前から精度を取得する。
		"""
		return cls[name.upper()]
	
	@classmethod
	def __class_getitem__(cls, item):
		"""
		名前から精度を取得するためのクラスメソッド。
		"""
		if isinstance(item, str):
			return cls[item]
		elif isinstance(item, slice):
			# スライスを使って精度の範囲を取得
			if not isinstance(item.start, str):
				raise TypeError("Slice start must be a string for DatePrecision")
			if not isinstance(item.stop, str):
				raise TypeError("Slice stop must be a string for DatePrecision")
			if item.step is not None and not isinstance(item.step, int):
				raise TypeError("Slice step must be an integer for DatePrecision")
			
			return cls.all()[cls[item.start.upper()]:cls[item.stop.upper()]:item.step or 1]
		else:
			raise TypeError(f"Invalid type for DatePrecision: {type(item)}")
	
	def __str__(self):
		"""
		精度を文字列で表現する。
		"""
		return self.name
	
	def __repr__(self):
		"""
		精度を文字列で表現する。
		"""
		return f"{self.__class__.__name__}.{self.name}"
