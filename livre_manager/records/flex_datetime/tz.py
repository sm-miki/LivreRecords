import re
from datetime import timedelta, tzinfo, timezone

from .error import FDInvalidFormatError
from .tz_map import TZ_MAP

class Timezone(tzinfo):
	AllTimezonesByAbbr = { }
	
	def __init__(self, offset: int, abbreviation: str = None, name: str = None):
		"""
		A class representing a timezone with its offset, abbreviation, and name.
		
		Args:
			offset (int): The UTC offset in minutes.
			abbreviation (str, optional): The timezone abbreviation (e.g., 'UTC', 'EST').
			name (str, optional): The full name of the timezone (e.g., 'Asia/Tokyo', 'America/New_York').
		"""
		self._offset = offset
		self._offset_str = self.format_offset(offset)
		self._abbreviation = abbreviation
		self._name = name
	
	@property
	def offset(self) -> int:
		"""Returns the UTC offset in minutes."""
		return self._offset
	
	@property
	def offset_str(self) -> str:
		"""Returns the string representation of the UTC offset."""
		return self._offset_str
	
	@property
	def abbreviation(self) -> str:
		"""Returns the timezone abbreviation."""
		return self._abbreviation
	
	@property
	def name(self) -> str:
		"""Returns the full name of the timezone."""
		return self._name
	
	def short_name(self, utc_prefix=True):
		return self._abbreviation if self._abbreviation else f"{'UTC' if utc_prefix else ''}{self._offset_str}"
	
	@staticmethod
	def format_offset(offset: int) -> str:
		"""
		Formats the UTC offset in a string format like '+HH:MM' or '-HH:MM'.
		
		Args:
			offset (int): The UTC offset in minutes.
		
		Returns:
			str: The formatted offset string.
		"""
		sign = '+' if offset >= 0 else '-'
		hours, minutes = divmod(abs(offset), 60)
		return f"{sign}{hours:02}:{minutes:02}"
	
	def __repr__(self):
		s = f"<Timezone UTC{self._offset_str}"
		if self._name:
			s += f" {repr(self._name)}"
			s += f" {repr(self._abbreviation)}"
		s += ">"
		return s
	
	def __str__(self):
		return self.name or self._abbreviation or f"UTC{self._offset_str}"
	
	def __eq__(self, other):
		if not isinstance(other, Timezone):
			return NotImplemented
		return (self._abbreviation == other._abbreviation and
				  self._offset == other._offset and
				  self._name == other._name)
	
	def __hash__(self):
		return hash((self._abbreviation, self._offset, self._name))
	
	# --- datetime.tzinfo interface methods ---
	
	def utcoffset(self, dt) -> timedelta:
		"""Returns the UTC offset as a timedelta object."""
		return timedelta(minutes=self._offset)
	
	def dst(self, dt) -> timedelta:
		"""Returns the daylight saving time (DST) adjustment. Not supported."""
		return timedelta(0)
	
	def tzname(self, dt) -> str:
		"""Returns the timezone name."""
		return self._name if self._name else f"UTC{self._offset_str}"
	
	# End of datetime.tzinfo interface methods
	
	@staticmethod
	def parse(s: str) -> 'Timezone':
		"""
		文字列からタイムゾーンをパースして返す。
		タイムゾーンの形式は以下のいずれか。
		 - タイムゾーン名形式（例: 'Asia/Tokyo', 'Europe/London' など）
		 - タイムゾーン略称形式（例: 'JST', 'UTC', 'EST' など）
		 - UTCオフセット形式（例: '+09:00', '-05:00', '+0900' など）
		 - 'Z'（UTCを表す）

		Args:
			 s (str): タイムゾーンを表す文字列。（例: 'Z', 'UTC', 'JST', '+09:00' など）
		Returns:
			 Timezone: パースされたタイムゾーンオブジェクト。
		Raises:
			 InvalidFormatError: 不明なフォーマット
		"""
		tz_input = s.lower()
		if tz := Timezone.AllTimezones.get(tz_input, None):
			# タイムゾーン名形式（Asia/Tokyoなど）
			return tz
		
		tz_input = s.upper()
		if tz_input == 'Z':
			return Timezone.AllTimezonesByAbbr['UTC']
		
		if tz := Timezone.AllTimezonesByAbbr.get(tz_input, None):
			# タイムゾーン略称形式（JST, UTCなど）
			return tz
		
		# +HH:MM／-HHMM 形式のパース
		m = re.match(r"^([+-])(\d{1,2}):?(\d{1,2})$", tz_input)
		if m:
			sign, hours, minutes = m.groups()
			offset = int(hours) * 60 + int(minutes)
			return Timezone(offset=-offset if sign == '-' else offset, abbreviation=None, name=None)
		
		raise FDInvalidFormatError(f"Unknown timezone format: \"{s}\"", details={ 'input': s })

# 既知のタイムゾーンの一覧
Timezone.AllTimezones = {
	tz_info['name'].lower(): Timezone(offset=tz_info['utcOffset'], abbreviation=tz_info['abbr'], name=tz_info['name'])
	for tz_info in TZ_MAP
}

# タイムゾーンの略称をキーとする辞書。
Timezone.AllTimezonesByAbbr = { tz.abbreviation: tz for tz in Timezone.AllTimezones.values() }
