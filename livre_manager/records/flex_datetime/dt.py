"""
flex-datetime
日付・日時文字列を、設定可能な精度とゼロパディングで解析・正規化するためのライブラリ。
"""
from typing import Union
import re
from datetime import datetime, date, timedelta

from .tz import Timezone
from .error import FDPrecisionError, FDInvalidTimezoneError, FDInvalidFormatError, FDInvalidValueError
from .precision import FDPrecision

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
				r"(?:"
					r"\s?(?P<tz>[a-zA-Z_]+|[+-]\d{1,2}:?\d{1,2})?"	# タイムゾーン
				r")?"
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

class FlexDatetime:
	"""
	精度付きの日時オブジェクトを表現するクラス。
	"""
	
	def __init__(self,
			precision: FDPrecision,
			year: int, month: Union[int | None] = None, day: Union[int | None] = None,
			hour: Union[int | None] = None, minute: Union[int | None] = None, second: Union[int | None] = None,
			tz: Union[Timezone | None] = None,
	):
		"""
		初期化メソッド。
		
		Args:
			precision (FDPrecision): 日時の精度。
			year (int): 年。
			month: (int | None, optional): 月。
			day: (int | None, optional): 日。
			hour: (int | None, optional): 時。
			minute: (int | None, optional): 分。
			second: (int | None, optional): 秒。
			tz: (Timezone | None, optional): タイムゾーン情報。
		"""
		self._precision = precision
		self._year = year
		self._month = month
		self._day = day
		self._hour = hour
		self._minute = minute
		self._second = second
		self._tz = tz
	
	@staticmethod
	def new(
			year: int, month: Union[int | None] = None, day: Union[int | None] = None,
			hour: Union[int | None] = None, minute: Union[int | None] = None, second: Union[int | None] = None,
			tz: Union[str | Timezone | None] = None,
	):
		"""
		新しいFlexDatetimeオブジェクトを生成する。
		
		Args:
			year (int): 年。
			month: (int | None, optional): 月。
			day: (int | None, optional): 日。
			hour: (int | None, optional): 時。
			minute: (int | None, optional): 分。
			second: (int | None, optional): 秒。
			tz: (str | Timezone | None, optional): タイムゾーン情報。

		Returns:
			FlexDatetime: 新しいFlexDatetimeオブジェクト。
		"""
		tz = Timezone.parse(tz) if isinstance(tz, str) else tz
		now = datetime.now(tz=tz)
		
		parts = {
			'year': year, 'month': month, 'day': day,
			'hour': hour, 'minute': minute, 'second': second
		}
		i = 5
		while i > 0:
			p = FDPrecision.DatetimeOrder[i]
			if parts[p.name] is not None:
				precision = p
				
				# 精度範囲内の位に規定値を設定する
				now_parts = {
					'year': now.year, 'month': now.month, 'day': now.day,
					'hour': now.hour, 'minute': now.minute, 'second': now.second
				}
				parts = { **now_parts, **parts }
				break
			
			i -= 1
		else:
			precision = FDPrecision.Year
		
		return FlexDatetime(precision=precision, **parts, tz=tz)
	
	@property
	def precision(self) -> FDPrecision:
		"""
		日時の精度を返す。
		
		Returns:
			FDPrecision: 日時の精度。
		"""
		return self._precision
	
	@property
	def year(self):
		"""
		年を返す。
		
		Returns:
			int: 年。
		"""
		return self._year
	
	@property
	def month(self):
		"""
		月を返す。月が指定されていない場合はNone。
		Returns:
			int | None: 月。
		"""
		return self._month
	
	@property
	def day(self):
		"""
		日を返す。日が指定されていない場合はNone。
		Returns:
			int | None: 日。
		"""
		return self._day
	
	@property
	def hour(self):
		"""
		時間を返す。時間が指定されていない場合はNone。
		
		Returns:
			int | None: 時間。
		"""
		return self._hour
	
	@property
	def minute(self):
		"""
		分を返す。分が指定されていない場合はNone。
		
		Returns:
			int | None: 分。
		"""
		return self._minute
	
	@property
	def second(self):
		"""
		秒を返す。秒が指定されていない場合はNone。
		
		Returns:
			int | None: 秒。
		"""
		return self._second
	
	@property
	def tz(self):
		"""
		タイムゾーン情報を返す。タイムゾーンが指定されていない場合はNone。
		Returns:
			Timezone | None: タイムゾーン情報。
		"""
		return self._tz
	
	def __repr__(self):
		"""
		オブジェクトの文字列表現を返す。
		
		Returns:
			str: オブジェクトの文字列表現。
		"""
		s = f"FlexDatetime(precision={self._precision}, year={self._year}"
		if self._month is not None:
			s += f", month={self._month}"
		if self._day is not None:
			s += f", day={self._day}"
		if self._hour is not None:
			s += f", hour={self._hour}"
		if self._minute is not None:
			s += f", minute={self._minute}"
		if self._second is not None:
			s += f", second={self._second}"
		if self._tz is not None:
			s += f", tz={self._tz}"
		s += ")"
		return s
	
	@staticmethod
	def parse(
			source, required_precision='year', accept_mixed_sep=True
	) -> 'FlexDatetime':
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
		in_precision = FDPrecision.Second
		for prec in FDPrecision.DatetimeOrder[1:]:
			if g[prec.name] is None:
				in_precision = FDPrecision.DatetimeOrder[prec.index - 1]
				break
		
		# 要求精度に対する検証
		if required_precision and required_precision != 'year':
			try:
				required_precision_obj = FDPrecision.Items[required_precision]
			except KeyError:
				raise FDInvalidValueError(f"Unknown required_precision: {required_precision}", details={ 'input': source, 'required_precision': required_precision })
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
				tz_info = Timezone.parse(tz_str)
			except FDInvalidFormatError as e:
				raise FDInvalidTimezoneError(f"Invalid timezone format: \"{g['tz']}\"", details={ 'input': source, 'timezone': g['tz'] }) from e
		
		return FlexDatetime(
			precision=in_precision,
			year=year, month=month, day=day,
			hour=hour, minute=minute, second=second,
			tz=tz_info,
		)
	
	@staticmethod
	def parse_date(source, required_precision='year', accept_mixed_sep=True) -> 'FlexDatetime':
		"""
		日付文字列を解析し、FlexDatetimeオブジェクトを生成する。
		
		Args:
			source (str): 日付文字列。
			required_precision: ('year'|'month'|'day', optional): 入力文字列に要求される最小精度。
			accept_mixed_sep (bool, optional): 日付の区切り文字が混在している場合に許可するかどうか。Defaults to True.

		Returns:
			FlexDatetime: 解析された日付オブジェクト。
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
		in_precision = FDPrecision.Day
		for p in FDPrecision.DateOrder:
			if g[p.name] is None:
				in_precision = FDPrecision.DateOrder[p.index - 1]
				break
		
		# 要求精度に対する検証
		if required_precision and required_precision != 'year':
			try:
				required_precision_obj = FDPrecision.Items[required_precision]
			except KeyError:
				raise FDInvalidValueError(f"Unknown required_precision: {required_precision}", details={ 'input': source, 'required_precision': required_precision })
			
			if required_precision > FDPrecision.Day:
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
		
		return FlexDatetime(
			precision=in_precision,
			year=year, month=month, day=day,
		)
	
	def apply_timezone(self, tz: Union[str | Timezone]):
		"""
		指定されたタイムゾーンを適用します。タイムゾーンが既に設定されている場合、変更は適用されません。

		Args:
			tz (str | Timezone): タイムゾーン文字列またはTimezoneオブジェクト。
		Returns:
			FlexDatetime: タイムゾーンが適用された新しいFlexDatetimeオブジェクト。
		"""
		if self._tz:
			return self
		elif isinstance(tz, str):
			tz = Timezone.parse(tz)
		
		return FlexDatetime(
			precision=self._precision,
			year=self._year, month=self._month, day=self._day,
			hour=self._hour, minute=self._minute, second=self._second,
			tz=tz,
		)
	
	def format(self, format: str = '%Y/%m/%d %H:%M:%S %z') -> str:
		"""
		日時を指定されたフォーマットで文字列に変換します。

		Args:
			format (str, optional): フォーマット文字列。デフォルトは '%Y/%m/%d %H:%M:%S'。

		Returns:
			str: フォーマットされた日時文字列。
		"""
		dt = self.to_datetime()
		if tz := self._tz:
			format = format.replace('%t', tz.short_name(utc_prefix=False))  # %t: タイムゾーンの短縮名(UTCプレフィックスなし)
			format = format.replace('%T', tz.short_name(utc_prefix=True))  # %t: タイムゾーンの短縮名
			format = format.replace('%o', tz.offset_str)  # %O: コロン付きオフセット(UCTプレフィックスなし)
			format = format.replace('%O', 'UTC' + tz.offset_str)  # %O: コロン付きオフセット
		else:
			format = format.replace('%t', '')  # %t: タイムゾーンの短縮名(UTCプレフィックスなし)
			format = format.replace('%T', '')  # %t: タイムゾーンの短縮名
			format = format.replace('%o', '')  # %O: コロン付きオフセット(UCTプレフィックスなし)
			format = format.replace('%O', '')  # %O: コロン付きオフセット
		
		return dt.strftime(format)
	
	def normalize(self,
			zero_pad=True,
			min_precision=None,
			date_sep='/',
			time_sep=':',
			force_tz=False,
			default_tz='UTC',
			utc_prefix=False,
	):
		"""
		日付時刻文字列を一貫した形式に正規化します。

		Args:
			zero_pad (bool, optional): 月、日、時、分、秒をゼロパディングするかどうか。
			min_precision ('year'|'month'|'day'|'hour'|'minute'|'second'|None, optional):
				出力が保証される最小精度。Noneの場合、入力の精度を維持する。
			date_sep (str, optional): 日付の区切り文字。規定値は '/'。
			time_sep (str, optional): 時刻の区切り文字。規定値は ':'。
			force_tz (bool, optional): タイムゾーンが指定されていない場合にデフォルトタイムゾーンを強制的に適用するかどうか。
			default_tz (str, optional): 入力文字列にタイムゾーンが含まれていない場合に適用されるデフォルトタイムゾーン。
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
				min_precision_obj = FDPrecision.Items[min_precision]
			except KeyError:
				raise FDInvalidValueError(f"Unknown min_precision: {min_precision}", details={ 'datetime': self, 'min_precision': min_precision })
			if out_precision < min_precision_obj:
				out_precision = min_precision_obj
		
		# 文字列組み立て
		out = _pad(self._year, 4) if zero_pad else str(self._year)
		if out_precision >= FDPrecision.Month:
			out += date_sep + (_pad(self._month) if zero_pad else str(self._month))
		if out_precision >= FDPrecision.Day:
			out += date_sep + (_pad(self._day) if zero_pad else str(self._day))
		if out_precision >= FDPrecision.Hour:
			out += ' ' + (_pad(self._hour) if zero_pad else str(self._hour))
		if out_precision >= FDPrecision.Minute:
			out += time_sep + (_pad(self._minute) if zero_pad else str(self._minute))
		if out_precision >= FDPrecision.Second:
			out += time_sep + (_pad(self._second) if zero_pad else str(self._second))
		
		# タイムゾーン
		if self._tz:
			out += ' ' + self._tz.short_name(utc_prefix=utc_prefix)
		elif force_tz and default_tz is not None:
			try:
				normalized_default_tz = Timezone.parse(default_tz)
			except FDInvalidFormatError as e:
				raise FDInvalidTimezoneError(f"Default timezone format invalid: '{default_tz}'", details={ 'default_tz': default_tz }) from e
			else:
				out += ' ' + normalized_default_tz.short_name(utc_prefix=utc_prefix)
		return out
	
	def to_datetime(self):
		"""
		FlexDatetimeオブジェクトをdatetimeオブジェクトに変換する。
		
		Returns:
			datetime: 日時オブジェクト。
		"""
		tz = self._tz
		
		# Pythonのdatetimeは直接UTCオフセットを持つオブジェクトとして構築できる
		# naive datetimeを作成し、タイムゾーンオフセットを適用してUTC時刻を計算
		args = [
			self._year, self._month or 1, self._day or 1,
			self._hour or 0, self._minute or 0, self._second or 0
		]
		return datetime(*args, tzinfo=tz)

# --- 内部関数 ---

def _pad(val: int, length: int = 2) -> str:
	"""
	数値をゼロパディングして文字列に変換します。

	Args:
		 val (int): ゼロパディングする数値。
		 length (int, optional): パディング後の文字列の最小長。Defaults to 2.
	Returns:
		 str: ゼロパディングされた文字列。
	"""
	return str(val).zfill(length)
