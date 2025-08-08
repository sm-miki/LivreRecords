"""
タイムゾーンを表すクラスを定義する。
"""
import re
import datetime
from datetime import timedelta, tzinfo
from typing import Set, Optional, Sequence

from .error import FDValueError, FDTypeError, FDTimezoneFormatError, FDTimezoneValueError
from .tz_map import TZ_MAP

class FlexiTimezone(tzinfo):
	TZ_PATTERN = r"[a-zA-Z0-9/_:+-]+"
	_OFFSET_REGEX = re.compile(
		r"^(?P<utc>UTC)?(?P<sign>[+-])(?P<offset>(?P<hours>\d{1,2})(?P<sep>:)(?P<minutes>\d{1,2})|(?P<compact_offset>\d{1,4}))$",
		re.IGNORECASE
	)
	
	def __init__(self, offset: int, abbreviation: str = None, name: str = None):
		"""
		A class representing a timezone with its offset, abbreviation, and name.
		
		Args:
			offset (timedelta | int): The UTC offset in minutes.
			abbreviation (str, optional): The timezone abbreviation (e.g., 'UTC', 'EST').
			name (str, optional): The full name of the timezone (e.g., 'Asia/Tokyo', 'America/New_York').
		"""
		self._offset = timedelta(minutes=offset) if isinstance(offset, int) else offset
		self._sign = -1 if self._offset < timedelta(0) else 1
		self._hour_offset, self._min_offset = divmod(abs(offset), 60)
		self._abbreviation = abbreviation
		self._name = name
	
	@property
	def offset(self) -> timedelta:
		"""Returns the UTC offset."""
		return self._offset
	
	@property
	def hour_offset(self) -> int:
		"""Returns the hour part of the UTC offset."""
		return self._hour_offset
	
	def min_offset(self) -> int:
		"""Returns the minute part of the UTC offset."""
		return self._min_offset
	
	@property
	def abbreviation(self) -> str:
		"""Returns the timezone abbreviation."""
		return self._abbreviation
	
	@property
	def name(self) -> str:
		"""Returns the full name of the timezone."""
		return self._name
	
	def short_name(self, utc_prefix=True):
		return self._abbreviation if self._abbreviation else self.format_offset(utc_prefix=utc_prefix)
	
	def __repr__(self):
		s = f"<Timezone {self.format_offset()}"
		if self._name:
			s += f" {repr(self._name)}"
		if self._abbreviation:
			s += f" {repr(self._abbreviation)}"
		s += ">"
		return s
	
	def __str__(self):
		return self.name or self._abbreviation or self.format_offset()
	
	def __eq__(self, other):
		if not isinstance(other, FlexiTimezone):
			return NotImplemented
		return (
				self._abbreviation == other._abbreviation and
				self._offset == other._offset and
				self._name == other._name
		)
	
	def __hash__(self):
		return hash((self._abbreviation, self._offset, self._name))
	
	# --- datetime.tzinfo interface methods ---
	
	def utcoffset(self, dt) -> timedelta:
		"""Returns the UTC offset as a timedelta object."""
		return self._offset
	
	def dst(self, dt) -> timedelta:
		"""Returns the daylight saving time (DST) adjustment. Not supported."""
		return timedelta(0)
	
	def tzname(self, dt) -> str:
		"""Returns the timezone name."""
		return self._name if self._name else self.format_offset()
	
	# End of datetime.tzinfo interface methods
	
	def format_offset(self, utc_prefix=False, separator=':') -> str:
		"""
		Formats the UTC offset based on the specified type.
		
		Args:
			utc_prefix (bool): If True, adds 'UTC' prefix to the offset string.
			separator (str): The separator to use between hours and minutes.
		
		Returns:
			str: The formatted offset string.
		"""
		return f"{'UTC' if utc_prefix else ''}{'-' if self._sign < 0 else '+'}{self._hour_offset:02}{separator}{self._min_offset:02}"
	
	def try_format(self, tz_formats=('name', 'abbr', 'utc+hh:mm')):
		"""
		
		Args:
			tz_formats (str | Sequence[str], optional): タイムゾーン形式の優先順序。指定された順にタイムゾーン形式の適用を試みる。
				- 'name': タイムゾーン名形式。例: 'Asia/Tokyo', 'America/New_York' など。
				- 'abbr': タイムゾーン略称形式。例: 'JST', 'UTC' など。
				- '+hh:mm':	UTCオフセット拡張形式（コロン区切り）。例: '+09:00', '-05:00' など。
				- '+hhmm': UTCオフセット形式。例: '+0900', '-0500' など。
				- 'utc+hh:mm': 接頭辞付きUTCオフセット拡張形式（コロン区切り）。例: 'UTC+09:00' など。
				- 'utc+hhmm': 接頭辞付きUTCオフセット形式。例: 'UTC+0900' など。

		Returns:

		"""
		if isinstance(tz_formats, str):
			tz_formats = (tz_formats,)
		elif not isinstance(tz_formats, Sequence):
			# 不明な型の場合、エラーを送出
			raise FDTypeError(f"Invalid type {type(tz_formats)} for tz_formats.", details={ 'tz_formats': tz_formats })
		
		for tz_format in tz_formats:
			match tz_format:
				case 'name':
					if self.name:
						return self.name
				case 'abbr':
					if self.abbreviation:
						return self.abbreviation
				case '+hh:mm':
					return self.format_offset(utc_prefix=False, separator=':')
				case '+hhmm':
					return self.format_offset(utc_prefix=False, separator='')
				case 'utc+hh:mm':
					return self.format_offset(utc_prefix=True, separator=':')
				case 'utc+hhmm':
					return self.format_offset(utc_prefix=True, separator='')
				case _:
					# 不明なフォーマットの場合、エラーを送出
					raise FDValueError(f"Unknown tz_format {tz_format}", details={ 'datetime': self, 'tz_format': tz_format })
		
		# どのフォーマットも適用できなかった場合、エラーを送出
		raise FDValueError(
			f"None of the formats {tz_formats} available for {self}",
			details={ 'datetime': self, 'tz_formats': tz_formats }
		)
	
	@staticmethod
	def by_abbr(abbr):
		"""
		略称からタイムゾーンを取得する。

		Args:
			abbr (str): タイムゾーンの略称（例: 'JST', 'UTC' など）。

		Returns:
			FlexiTimezone: 該当するタイムゾーンオブジェクト。
		Raises:
			KeyError: 略称に対応するタイムゾーンが存在しない場合。
		"""
		tz = all_timezones_by_abbr.get(abbr.lower())
		if not tz:
			raise FDTimezoneValueError(f"Unknown timezone abbreviation: {abbr}")
		return tz
	
	@staticmethod
	def by_name(name):
		"""
		名前からタイムゾーンを取得する。

		Args:
			name (str): タイムゾーンの名前（例: 'Asia/Tokyo', 'America/New_York' など）。

		Returns:
			FlexiTimezone: 該当するタイムゾーンオブジェクト。
		Raises:
			KeyError: 名前に対応するタイムゾーンが存在しない場合。
		"""
		tz = all_timezones.get(name.lower())
		if not tz:
			raise FDTimezoneValueError(f"Unknown timezone name: {name}")
		return tz
	
	@staticmethod
	def parse(
			s: str,
			allowed_formats: Optional[Set[str]] = None,
	) -> 'FlexiTimezone':
		"""
		文字列からタイムゾーンをパースします。

		Args:
			s (str): タイムゾーンを表す文字列。（例: 'Z', 'UTC', 'JST', '+09:00' など）
			allowed_formats (set, optional): 許容するタイムゾーン形式の集合。Noneの場合は全てのフォーマットを許容します。
				- 'name': タイムゾーン名形式。例: 'Asia/Tokyo', 'America/New_York' など。
				- 'abbr': タイムゾーン略称形式。例: 'JST', 'UTC' など。
				- '+hh:mm':	UTCオフセット形式。例: '+09:00', '-05:00' など。
				- '+hhmm': UTCオフセット形式（コロン区切りなし）。例: '+0900', '-0500' など。
				- 'utc+hh:mm': 接頭辞付きUTCオフセット拡張形式。例: 'UTC+09:00' など。
				- 'utc+hhmm': 接頭辞付きUTCオフセット形式（コロン区切りなし）。例: 'UTC+0900' など。
				- 'z': 'Z'形式。UTCを表す。
		Returns:
			FlexiTimezone: パースされたタイムゾーンオブジェクト。
		"""
		if allowed_formats is None:
			allowed_formats = { 'name', 'abbr', 'z', '+hh:mm', '+hhmm', 'utc+hh:mm', 'utc+hhmm' }
		elif isinstance(allowed_formats, str):
			allowed_formats = { allowed_formats }
		else:
			allowed_formats = set(allowed_formats)
		
		tz_input = s.lower()
		if tz := all_timezones.get(tz_input, None):
			# タイムゾーン名形式（Asia/Tokyoなど）の場合
			if 'name' not in allowed_formats:
				raise FDTimezoneFormatError(
					f"Name-formatted timezone is not allowed according to allowed_formats {allowed_formats}. Include 'name' to allow it.",
					details={ 'input': s }
				)
			return tz
		
		if tz_input == 'z':
			if 'z' not in allowed_formats:
				raise FDTimezoneFormatError(
					f"Z-formatted timezone is not allowed according to allowed_formats {allowed_formats}. Include 'z' to allow it.",
					details={ 'input': s }
				)
			return all_timezones_by_abbr['utc']
		
		if tz := all_timezones_by_abbr.get(tz_input, None):
			# タイムゾーン略称形式（JST, UTCなど）
			if 'abbr' not in allowed_formats:
				raise FDTimezoneFormatError(
					f"Abbreviation-formatted timezone is not allowed according to allowed_formats {allowed_formats}. Include 'abbr' to allow it.",
					details={ 'input': s }
				)
			return tz
		
		# +HH:MM／-HHMM 形式のパース
		m = FlexiTimezone._OFFSET_REGEX.match(tz_input)
		if m:
			if m.group('sep'):
				if m.group('utc'):
					if 'utc+hh:mm' not in allowed_formats:
						raise FDTimezoneFormatError(f"Timezone format UTC+hh:mm is not allowed according to allowed_formats {allowed_formats}. Include 'utc+hh:mm' to allow it.", details={ 'input': s })
				else:
					if '+hh:mm' not in allowed_formats:
						raise FDTimezoneFormatError(f"Timezone format +hh:mm is not allowed according to allowed_formats {allowed_formats}. Include '+hh:mm' to allow it.", details={ 'input': s })
				
				hours = m.group('hours')
				minutes = m.group('minutes') or '0'
			else:
				if m.group('utc'):
					if 'utc+hhmm' not in allowed_formats:
						raise FDTimezoneFormatError(f"Timezone format UTC+hhmm is not allowed according to allowed_formats {allowed_formats}. Include 'utc+hhmm' to allow it.", details={ 'input': s })
				else:
					if '+hhmm' not in allowed_formats:
						raise FDTimezoneFormatError(f"Timezone format +hhmm is not allowed according to allowed_formats {allowed_formats}. Include '+hhmm' to allow it.", details={ 'input': s })
				
				offset_str = m.group('compact_offset')
				match len(offset_str):
					case 1 | 2:
						hours, minutes = offset_str, '0'
					case 3:
						hours, minutes = offset_str[0], offset_str[1:]
					case 4:
						hours, minutes = offset_str[:2], offset_str[2:]
			
			sign = m.group('sign')
			offset = int(hours) * 60 + int(minutes)
			
			return FlexiTimezone(offset=-offset if sign == '-' else offset, abbreviation=None, name=None)
		
		raise FDTimezoneFormatError(
			f"Invalid timezone format: {s}.",
			details={ 'input': s }
		)

# 既知のタイムゾーンの一覧
all_timezones = {
	tz_info['name'].lower(): FlexiTimezone(offset=tz_info['utcOffset'], abbreviation=tz_info['abbr'], name=tz_info['name'])
	for tz_info in TZ_MAP
}

# タイムゾーンの略称をキーとする辞書。
all_timezones_by_abbr = { tz.abbreviation.lower(): tz for tz in all_timezones.values() }
