"""
fuzzy_datetime.dt
精度付きの日時オブジェクトを表現するクラスを定義する。
"""
from typing import Union
import re
from datetime import datetime, date, timedelta

from .tz import FlexiTimezone
from .error import FDPrecisionError, FDInvalidTimezoneError, FDInvalidFormatError, FDInvalidValueError
from .precision import DatetimePrecision

# --- 正規表現パターン ---

# @formatter:off
datetime_reg = re.compile(
	r"^(?P<year>\d{4})"
	r"(?:"
		r"(?P<sep1>[/.-])(?P<month>\d{1,2})"
		r"(?:"
			r"(?P<sep2>[/.-])(?P<day>\d{1,2})"
			r"(?:"
				r"[ T](?P<hour>\d{1,2})"
				r"(?:"
					r"(?P<sep3>[:.-])(?P<minute>\d{1,2})"
					r"(?:"
						r"(?P<sep4>[:.-])(?P<second>\d{1,2})"
					r")?"
				r")?"
			r")?"
			r"(?:"
				r"\s?(?P<tz>[a-zA-Z_]+|(?:UTC)?[+-]\d{1,2}:?\d{1,2}|[a-zA-Z]+/[a-zA-Z_]+)?"	# タイムゾーン
			r")?"
		r")?"
	r")?$"
)
date_reg = re.compile(
	r"^(?P<year>\d{4})"
	r"(?:"
		r"(?P<sep1>[/.-])(?P<month>\d{1,2})"
		r"(?:"
			r"(?P<sep2>[/.-])(?P<day>\d{1,2})T?"
		r")?"
	r")?$"
)
# @formatter:on

class FuzzyDatetime:
	"""
	精度付きの日時オブジェクトを表現するクラス。
	"""
	
	def __init__(self,
			year: int, month: Union[int | None] = None, day: Union[int | None] = None,
			hour: Union[int | None] = None, minute: Union[int | None] = None, second: Union[int | None] = None,
			tzinfo: Union[FlexiTimezone | None] = None,
			precision: Union[DatetimePrecision | None] = None,
	):
		"""
		初期化メソッド。

		Args:
			precision (DatetimePrecision): 日時の精度。
			year (int): 年。
			month: (int | None, optional): 月。
			day: (int | None, optional): 日。
			hour: (int | None, optional): 時。
			minute: (int | None, optional): 分。
			second: (int | None, optional): 秒。
			tzinfo: (Timezone | None, optional): タイムゾーン情報。
		"""
		self._precision = precision or self._assume_precision(year, month, day, hour, minute, second)
		self._year = year
		self._month = month or 1
		self._day = day or 1
		self._hour = hour or 0
		self._minute = minute or 0
		self._second = second or 0
		self._tzinfo = tzinfo
	
	@staticmethod
	def _assume_precision(
			year: int, month: Union[int | None] = None, day: Union[int | None] = None,
			hour: Union[int | None] = None, minute: Union[int | None] = None, second: Union[int | None] = None
	) -> DatetimePrecision:
		"""
		指定された日時の精度を推定する。
		
		Args:
			year (int): 年。
			month: (int | None, optional): 月。
			day: (int | None, optional): 日。
			hour: (int | None, optional): 時。
			minute: (int | None, optional): 分。
			second: (int | None, optional): 秒。

		Returns:
			DatetimePrecision: 推定された日時の精度。
		"""
		if second is not None:
			return DatetimePrecision.Second
		elif minute is not None:
			return DatetimePrecision.Minute
		elif hour is not None:
			return DatetimePrecision.Hour
		elif day is not None:
			return DatetimePrecision.Day
		elif month is not None:
			return DatetimePrecision.Month
		else:
			return DatetimePrecision.Year
	
	@property
	def precision(self) -> DatetimePrecision:
		"""
		日時の精度を返す。
		
		Returns:
			DatetimePrecision: 日時の精度。
		"""
		return self._precision
	
	@property
	def year(self) -> int:
		"""
		年を返す。
		
		Returns:
			int: 年。
		"""
		return self._year
	
	@property
	def month(self) -> int:
		"""
		月を返す。月が指定されていない場合はNone。
		Returns:
			int | None: 月。
		"""
		return self._month
	
	@property
	def day(self) -> int:
		"""
		日を返す。日が指定されていない場合はNone。
		Returns:
			int | None: 日。
		"""
		return self._day
	
	@property
	def hour(self) -> int:
		"""
		時間を返す。時間が指定されていない場合はNone。
		
		Returns:
			int | None: 時間。
		"""
		return self._hour
	
	@property
	def minute(self) -> int:
		"""
		分を返す。分が指定されていない場合はNone。
		
		Returns:
			int | None: 分。
		"""
		return self._minute
	
	@property
	def second(self) -> int:
		"""
		秒を返す。秒が指定されていない場合はNone。
		
		Returns:
			int | None: 秒。
		"""
		return self._second
	
	@property
	def tzinfo(self) -> Union[FlexiTimezone, None]:
		"""
		タイムゾーン情報を返す。タイムゾーンが指定されていない場合はNone。
		Returns:
			FlexiTimezone | None: タイムゾーン情報。
		"""
		return self._tzinfo
	
	def __repr__(self):
		"""
		オブジェクトの文字列表現を返す。
		
		Returns:
			str: オブジェクトの文字列表現。
		"""
		s = f"FlexDatetime(precision={repr(self._precision)}, year={self._year}"
		
		part_funcs = [
			lambda: f", month={self._month}",
			lambda: f", day={self._day}",
			lambda: f", hour={self._hour}",
			lambda: f", minute={self._minute}",
			lambda: f", second={self._second}",
		]
		for part in part_funcs[:self.precision.index]:
			s += part()
		
		if self._tzinfo is not None:
			s += f", tz={self._tzinfo}"
		s += ")"
		return s
	
	@staticmethod
	def parse(
			source,
			required_precision: Union[str, DatetimePrecision] = 'year',
			accept_mixed_sep=True
	) -> 'FuzzyDatetime':
		"""
		日時文字列を解析し、FlexDatetimeオブジェクトを生成する。

		Args:
			source (str): 日時文字列。
			required_precision: ('year'|'month'|'day'|'hour'|'minute'|'second', optional): 入力文字列に要求される最小精度。
			accept_mixed_sep (bool, optional): 日付と時刻の区切り文字が混在している場合に許可するかどうか。

		Returns:
			str: 正規化された日付時刻文字列。
		"""
		m = datetime_reg.match(source)
		if not m:
			raise FDInvalidFormatError(f"Invalid datetime format: \"{source}\"", details={ 'input': source })
		g = m.groupdict()
		
		# 入力の日時精度の特定
		in_precision = DatetimePrecision.Second
		for prec in DatetimePrecision.DatetimeOrder[1:]:
			if g[prec.name] is None:
				in_precision = DatetimePrecision.DatetimeOrder[prec.index - 1]
				break
		
		# 要求精度に対する検証
		if required_precision and required_precision != 'year':
			if isinstance(required_precision, str):
				try:
					required_precision_obj = DatetimePrecision.Items[required_precision]
				except KeyError:
					raise FDInvalidValueError(f"Unknown required_precision: {required_precision}", details={ 'input': source, 'required_precision': required_precision })
			else:
				required_precision_obj = required_precision
			
			if in_precision < required_precision_obj:
				raise FDPrecisionError(f"Precision not met ({required_precision}) for \"{source}\"", details={ 'input': source, 'required_precision': required_precision })
		
		# 区切り記号の検証
		if not accept_mixed_sep:
			if g.get('sep1') and g.get('sep2') and g['sep1'] != g['sep2']:
				raise FDInvalidFormatError(f"Mixed date separators in \"{source}\"", details={ 'input': source, 'sep1': g['sep1'], 'sep2': g['sep2'] })
			if g.get('sep3') and g.get('sep4') and g['sep3'] != g['sep4']:
				raise FDInvalidFormatError(f"Mixed time separators in \"{source}\"", details={ 'input': source, 'sep3': g['sep3'], 'sep4': g['sep4'] })
		
		# 数値に変換
		year = int(g['year'])
		month = int(g['month']) if g['month'] else None
		day = int(g['day']) if g['day'] else None
		hour = int(g['hour']) if g['hour'] else None
		minute = int(g['minute']) if g['minute'] else None
		second = int(g['second']) if g['second'] else None
		
		# 値の検証
		if not (1 <= year <= 9999):
			raise FDInvalidValueError(f"Year out of range: {year}", details={ 'input': source, 'year': year })
		if month is not None:
			if not (1 <= month <= 12):
				raise FDInvalidValueError(f"Month out of range: {month}", details={ 'input': source, 'month': month })
			
			# Pythonのdatetime.dateオブジェクトを使って月の日数を取得
			try:
				# date(year, month, 1)でその月の最初の日、timedelta(days=-1)で前の月の最後の日を取得
				# これにより、指定した月の最終日（日数）を取得できる
				days_in_month = (date(year, month + 1, 1) - timedelta(days=1)).day \
					if month < 12 else (date(year + 1, 1, 1) - timedelta(days=1)).day
			except ValueError:  # 例: 存在しない日付 (2月30日など) の場合
				raise FDInvalidValueError(f"Invalid date combination: {year}-{month}-{day}", details={ 'input': source })
			
			if day is not None:
				if not (1 <= day <= days_in_month):
					raise FDInvalidValueError(f"Day out of range: {day}", details={ 'input': source, 'day': day })
				if hour is not None:
					if not (0 <= hour <= 23):
						raise FDInvalidValueError(f"Hour out of range: {hour}", details={ 'input': source, 'hour': hour })
					if minute is not None:
						if not (0 <= minute <= 59):
							raise FDInvalidValueError(f"Minute out of range: {minute}", details={ 'input': source, 'minute': minute })
						if second is not None and not (0 <= second <= 59):
							raise FDInvalidValueError(f"Second out of range: {second}", details={ 'input': source, 'second': second })
		
		# タイムゾーンの検証
		tz_info = None
		if tz_str := g.get('tz'):
			try:
				tz_info = FlexiTimezone.parse(tz_str)
			except FDInvalidFormatError as e:
				raise FDInvalidTimezoneError(f"Invalid timezone format: \"{g['tz']}\"", details={ 'input': source, 'timezone': g['tz'] }) from e
		
		return FuzzyDatetime(
			year=year, month=month, day=day,
			hour=hour, minute=minute, second=second,
			tzinfo=tz_info,
			precision=in_precision,
		)
	
	@staticmethod
	def parse_date(
			source,
			required_precision: Union[str | DatetimePrecision] = 'year',
			accept_mixed_sep=True
	) -> 'FuzzyDatetime':
		"""
		日付文字列を解析し、FlexDatetimeオブジェクトを生成する。
		
		Args:
			source (str): 日付文字列。
			required_precision: ('year'|'month'|'day', optional): 入力文字列に要求される最小精度。
			accept_mixed_sep (bool, optional): 日付の区切り文字が混在している場合に許可するかどうか。Defaults to True.

		Returns:
			FuzzyDatetime: 解析された日付オブジェクト。
		Raises:
			FDInvalidFormatError: 入力文字列のフォーマットが無効な場合。
			FDInvalidValueError: 入力値が無効な場合（例:月や日が範囲外）。
			FDPrecisionError: 要求された精度が満たされていない場合。
			FDInvalidTimezoneError: タイムゾーンのフォーマットが無効な場合。
		"""
		m = date_reg.match(source)
		if not m:
			raise FDInvalidFormatError(f"Invalid date format: \"{source}\"", details={ 'input': source })
		g = m.groupdict()
		
		# 入力の日時精度の特定
		in_precision = DatetimePrecision.Day
		for p in DatetimePrecision.DateOrder:
			if g[p.name] is None:
				in_precision = DatetimePrecision.DateOrder[p.index - 1]
				break
		
		# 要求精度に対する検証
		if required_precision and required_precision != 'year':
			if isinstance(required_precision, str):
				try:
					required_precision_obj = DatetimePrecision.Items[required_precision]
				except KeyError:
					raise FDInvalidValueError(f"Unknown required_precision: {required_precision}", details={ 'input': source, 'required_precision': required_precision })
			else:
				required_precision_obj = required_precision
			
			if required_precision_obj > DatetimePrecision.Day:
				raise FDInvalidValueError(f"Invalid required_precision: {required_precision}", details={ 'input': source, 'required_precision': required_precision })
			
			if in_precision < required_precision_obj:
				raise FDPrecisionError(f"Precision not met ({required_precision}) for \"{source}\"", details={ 'input': source, 'required_precision': required_precision })
		
		# 区切り記号の検証
		if not accept_mixed_sep:
			if g.get('sep1') and g.get('sep2') and g['sep1'] != g['sep2']:
				raise FDInvalidFormatError(f"Mixed date separators in \"{source}\"", details={ 'input': source, 'sep1': g['sep1'], 'sep2': g['sep2'] })
		
		# 数値に変換
		year = int(g['year'])
		month = int(g['month']) if g['month'] else None
		day = int(g['day']) if g['day'] else None
		
		# 値の検証
		if month is not None:
			if not (1 <= month <= 12):
				raise FDInvalidValueError(f"Month out of range: {month}", details={ 'input': source, 'month': month })
			
			# Pythonのdatetime.dateオブジェクトを使って月の日数を取得
			try:
				# date(year, month, 1)でその月の最初の日、timedelta(days=-1)で前の月の最後の日を取得
				# これにより、指定した月の最終日（日数）を取得できる
				days_in_month = (date(year, month + 1, 1) - timedelta(days=1)).day \
					if month < 12 else (date(year + 1, 1, 1) - timedelta(days=1)).day
			except ValueError:  # 例: 存在しない日付 (2月30日など) の場合
				raise FDInvalidValueError(f"Invalid date combination: {year}-{month}-{day}", details={ 'input': source })
			
			if day is not None:
				if not (1 <= day <= days_in_month):
					raise FDInvalidValueError(f"Day out of range: {day}", details={ 'input': source, 'day': day })
		
		return FuzzyDatetime(
			year=year, month=month, day=day,
			precision=in_precision,
		)
	
	def apply_timezone(self, tz: Union[str | FlexiTimezone]):
		"""
		指定されたタイムゾーンを適用する。タイムゾーンが既に設定されている場合、変更は適用されません。

		Args:
			tz (str | FlexiTimezone): タイムゾーン文字列またはTimezoneオブジェクト。
		Returns:
			FuzzyDatetime: タイムゾーンが適用された新しいFlexDatetimeオブジェクト。
		"""
		if self._tzinfo:
			return self
		elif isinstance(tz, str):
			tz = FlexiTimezone.parse(tz)
		
		return FuzzyDatetime(
			year=self._year, month=self._month, day=self._day,
			hour=self._hour, minute=self._minute, second=self._second,
			tzinfo=tz,
			precision=self._precision,
		)
	
	def format(self, format: str = '%Y/%m/%d %H:%M:%S %z') -> str:
		"""
		日時を指定されたフォーマットで文字列に変換する。

		Args:
			format (str, optional): フォーマット文字列。デフォルトは '%Y/%m/%d %H:%M:%S'。

		Returns:
			str: フォーマットされた日時文字列。
		"""
		dt = self.to_datetime()
		if tz := self._tzinfo:
			format = format.replace('%t', tz.short_name(utc_prefix=False))  # %t: タイムゾーンの短縮名(UTCプレフィックスなし。+09:00、JSTなど)
			format = format.replace('%T', tz.short_name(utc_prefix=True))  # %T: タイムゾーンの短縮名(UTC+09:00、JSTなど)
			format = format.replace('%o', tz.offset_str)  # %O: コロン付きオフセット(UCTプレフィックスなし)
			format = format.replace('%O', 'UTC' + tz.offset_str)  # %O: コロン付きオフセット
		else:
			format = format.replace('%t', '')  # %t: タイムゾーンの短縮名(UTCプレフィックスなし)
			format = format.replace('%T', '')  # %T: タイムゾーンの短縮名
			format = format.replace('%o', '')  # %o: コロン付きオフセット(UCTプレフィックスなし)
			format = format.replace('%O', '')  # %O: コロン付きオフセット
		
		return dt.strftime(format)
	
	def normalize(self,
			zero_pad=True,
			min_precision=None,
			date_sep='/',
			time_sep=':',
			force_tz=False,
			utc_prefix=False,
	):
		"""
		日付時刻文字列を一貫した形式に正規化する。

		Args:
			zero_pad (bool, optional): 月、日、時、分、秒をゼロパディングするかどうか。
			min_precision ('year'|'month'|'day'|'hour'|'minute'|'second'|None, optional):
				出力が保証される最小精度。Noneの場合、入力の精度を維持する。
			date_sep (str, optional): 日付の区切り文字。規定値は '/'。
			time_sep (str, optional): 時刻の区切り文字。規定値は ':'。
			force_tz (bool, optional): タイムゾーンが指定されていない場合にデフォルトタイムゾーンを強制的に適用するかどうか。
			utc_prefix (bool, optional): trueを指定した場合、タイムゾーンがUTCオフセットで表される場合に "UTC" のプレフィックスを付ける。
		Returns:
			 str: 正規化された日付時刻文字列。
		Raises:
			 DateTimeError:
		"""
		# 出力すべき日時精度の決定
		out_precision = self._precision
		if min_precision is not None:
			try:
				min_precision_obj = DatetimePrecision.Items[min_precision]
			except KeyError:
				raise FDInvalidValueError(f"Unknown min_precision: {min_precision}", details={ 'datetime': self, 'min_precision': min_precision })
			if out_precision < min_precision_obj:
				out_precision = min_precision_obj
		
		# 文字列組み立て
		out = _pad(self._year, 4) if zero_pad else str(self._year)
		parts_configs = [
			(self.month, 2, date_sep),
			(self.day, 2, date_sep),
			(self.hour, 2, ' '),
			(self.minute, 2, time_sep),
			(self.second, 2, time_sep),
		]
		for part, length, sep in parts_configs[:out_precision.index]:
			out += sep + (_pad(part, length) if zero_pad else str(part))
		
		# タイムゾーン
		if self._tzinfo:
			out += ' ' + self._tzinfo.short_name(utc_prefix=utc_prefix)
		
		return out
	
	def to_date(self) -> date:
		"""
		FlexDatetimeオブジェクトをdateオブジェクトに変換する。
		
		Returns:
			date: 日付オブジェクト。
		"""
		return date(self._year, self._month, self._day)
	
	def to_datetime(self):
		"""
		FlexDatetimeオブジェクトをdatetimeオブジェクトに変換する。
		
		Returns:
			datetime: 日時オブジェクト。
		"""
		tz = self._tzinfo
		
		# Pythonのdatetimeは直接UTCオフセットを持つオブジェクトとして構築できる
		# naive datetimeを作成し、タイムゾーンオフセットを適用してUTC時刻を計算
		return datetime(
			self._year, self._month, self._day,
			self._hour, self._minute, self._second,
			tzinfo=tz,
		)
	
	def to_isoformat(self, sep='T', timespec='auto') -> str:
		"""
		FlexDatetimeオブジェクトをISO 8601形式の文字列に変換する。

		Args:
			sep (str, optional): 日付と時刻の区切り文字。デフォルトは 'T'。
			timespec (str, optional): 時刻の精度。'auto'、'seconds'、'milliseconds'、'microseconds' のいずれか。

		Returns:
			str: ISO 8601形式の日時文字列。
		"""
		dt = self.to_datetime()
		return dt.isoformat(sep=sep, timespec=timespec)
	
	def __str__(self):
		"""
		FlexDatetimeオブジェクトの文字列表現を返す。
		
		Returns:
			str: 日時の文字列表現。
		"""
		return self.normalize(
			zero_pad=True,
			min_precision=None,
			date_sep='/',
			time_sep=':',
			force_tz=False,
			utc_prefix=False,
		)

# --- 内部関数 ---

def _pad(val: int, length: int = 2) -> str:
	"""
	数値をゼロパディングして文字列に変換する。

	Args:
		 val (int): ゼロパディングする数値。
		 length (int, optional): パディング後の文字列の最小長。
	Returns:
		 str: ゼロパディングされた文字列。
	"""
	return str(val).zfill(length)
