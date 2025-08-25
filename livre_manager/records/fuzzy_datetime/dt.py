"""
fuzzy_datetime.dt
精度付きの日時オブジェクトを表現するクラスを定義する。
"""
from typing import Sequence, Set, Optional
import re
from datetime import datetime, date, timedelta
import calendar

from .tz import FlexiTimezone
from .error import FDPrecisionError, FDFormatError, FDValueError, FDTypeError, FDTimezoneFormatError
from .precision import DatePrecision

# --- 正規表現パターン ---

# @formatter:off
DATETIME_REG = re.compile(
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
					rf"\s?(?P<tz>{FlexiTimezone.TZ_PATTERN})"	# タイムゾーン
				r")?"
			r")?"
		r")?"
	r")?$"
)
DATE_REG = re.compile(
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
			year: int,
			month: Optional[int] = None,
			day: Optional[int] = None,
			hour: Optional[int] = None,
			minute: Optional[int] = None,
			second: Optional[int] = None,
			tzinfo: Optional[FlexiTimezone] = None,
			precision: Optional[DatePrecision] = None,
	):
		"""
		初期化メソッド。
		指定された日時の構成要素とタイムゾーン情報を使用して、FuzzyDatetimeオブジェクトを生成します。
		precision 引数を指定しない場合、指定された日時の値から自動的に精度を推論します。
		precision 引数を指定した場合、その精度以下の位の値を指定する必要があります。ただし、時、分、秒の値を省略した場合は0で初期化されます。

		Args:
			year (int): 年。
			month: (int, optional): 月。
			day: (int, optional): 日。
			hour: (int, optional): 時。
			minute: (int, optional): 分。
			second: (int, optional): 秒。
			tzinfo: (Timezone, optional): タイムゾーン情報。
			precision (DatePrecision): 日時の精度。
		"""
		# self._components = (year, month, day, hour, minute, second)
		self._components, self._precision = self._determine_precision(
			[year, month, day, hour, minute, second], precision
		)
		self._tzinfo = tzinfo
		
		# self._determine_precision(precision)
		self._validate_datetime()
	
	def _determine_precision(
			self, components: list[int], precision: str | DatePrecision
	) -> tuple[tuple[int, ...], DatePrecision]:
		"""
		精度に応じて日時の構成要素のヌル性および値の範囲を検証する。

		Args:
			precision (str | DatePrecision): 日時の精度。指定しない場合は自動的に推論される。
		"""
		if precision:
			if isinstance(precision, str):
				try:
					precision = DatePrecision.by_name(precision)
				except KeyError as e:
					# 精度として無効な文字列が指定された場合
					raise FDValueError(f"Unknown precision: {precision}", details={ 'input': precision }) from e
			
			# 精度以上の値が設定されていないか検証する
			for i in range(precision + 1, len(DatePrecision)):
				if components[i] is not None:
					# 指定された精度よりも高い位が設定されている場合
					raise FDPrecisionError(
						f"{DatePrecision(i)} component cannot be set for precision {precision}",
						details={
							'precision': precision,
							'year': self.year, 'month': self.month, 'day': self.day,
							'hour': self.hour, 'minute': self.minute, 'second': self.second,
						}
					)
		else:
			# 精度の推論
			for i in range(len(DatePrecision) - 1, 0, -1):
				if components[i] is not None:
					precision = DatePrecision(i)
					break
			else:
				precision = DatePrecision.YEAR
		
		# 精度以下の構成要素が設定されていることを確認する（年、月、日のみ）
		for i in range(min(DatePrecision.HOUR, precision + 1)):
			if components[i] is None:
				# 指定された精度以下の位が設定されていない場合
				raise FDPrecisionError(
					f"Missing {DatePrecision(i)} component for precision {self._precision}",
					details={
						'precision': self._precision,
						'year': self.year, 'month': self.month, 'day': self.day,
						'hour': self.hour, 'minute': self.minute, 'second': self.second,
					}
				)
		
		# 精度以下の位に規定値を設定する（時、分、秒のみ）
		for j in range(i, precision + 1):
			if components[j] is None:
				components[j] = 0
		
		return tuple(components), precision
	
	def _validate_datetime(self):
		# 値の範囲の検証
		
		# 年の範囲の検証
		if not (1 <= self.year <= 9999):
			raise FDValueError(f"Year {self.year} is out of range.", details={ 'year': self.year })
		
		if self.month is not None:
			# 月の範囲の検証
			if not (1 <= self.month <= 12):
				raise FDValueError(f"Month {self.month} is out of range.", details={ 'month': self.month })
			
			if self.day is not None:
				# 月の日数を取得
				days_in_month = calendar.monthrange(self.year, self.month)[1]
				
				# 日の範囲の検証
				if not (1 <= self.day <= days_in_month):
					raise FDValueError(f"Day {self.day} is out of range for the month {self.year}/{self.month}.",
											 details={ 'year': self.year, 'month': self.month, 'day': self.day })
				
				if self.hour is not None:
					# 時の範囲の検証
					if not (0 <= self.hour <= 23):
						raise FDValueError(f"Hour {self.hour} is out of range.", details={ 'hour': self.hour })
					
					if self.minute is not None:
						# 分の範囲の検証
						if not (0 <= self.minute <= 59):
							raise FDValueError(f"Minute {self.minute} is out of range.", details={ 'minute': self.minute })
						
						# 秒の範囲の検証
						if self.second is not None and not (0 <= self.second <= 59):
							raise FDValueError(f"Second {self.second} is out of range.", details={ 'second': self.second })
	
	@property
	def precision(self) -> DatePrecision:
		"""
		日時の精度を返す。
		
		Returns:
			DatePrecision: 日時の精度。
		"""
		return self._precision
	
	@property
	def year(self) -> int:
		"""
		年を取得します。
		
		Returns:
			int: 年の値。
		"""
		return self._components[0]
	
	@property
	def month(self) -> int:
		"""
		月を取得します。precision < DatePrecision.MONTH の場合は None を返します。
		
		Returns:
			int | None: 月の位の値。
		"""
		return self._components[1]
	
	@property
	def day(self) -> int:
		"""
		日を取得します。precision < DatePrecision.DAY の場合は None を返します。
		
		Returns:
			int | None: 日の位の値。
		"""
		return self._components[2]
	
	@property
	def hour(self) -> int:
		"""
		時間を取得します。precision < DatePrecision.HOUR の場合は None を返します。
		
		Returns:
			int | None: 時間の位の値。
		"""
		return self._components[3]
	
	@property
	def minute(self) -> int:
		"""
		分を取得します。precision < DatePrecision.MINUTE の場合は None を返します。
		
		Returns:
			int | None: 分の位の値。
		"""
		return self._components[4]
	
	@property
	def second(self) -> int:
		"""
		秒を取得します。precision < DatePrecision.SECOND の場合は None を返します。
		
		Returns:
			int | None: 秒の位の値。
		"""
		return self._components[5]
	
	@property
	def tzinfo(self) -> FlexiTimezone | None:
		"""
		タイムゾーン情報を取得します。タイムゾーンが指定されていない場合は None を返します。
		Returns:
			FlexiTimezone | None: タイムゾーン情報。
		"""
		return self._tzinfo
	
	@property
	def components(self) -> tuple[int | None]:
		"""
		日時の構成要素を取得します。
		
		Returns:
			tuple[int | None]: 年、月、日、時間、分、秒の順に並んだ構成要素のリスト。
		"""
		return self._components
	
	def __repr__(self):
		"""
		オブジェクトの文字列表現を取得します。
		
		Returns:
			str: オブジェクトの文字列表現。
		"""
		s = f"FuzzyDatetime(precision={repr(self._precision)}"
		
		s += ''.join(f", {prec.name.lower()}={value}" for prec, value in zip(
			DatePrecision.slice(None, self.precision + 1),
			self._components[:self.precision + 1]
		))
		
		if self._tzinfo is not None:
			s += f", tz={self._tzinfo}"
		s += ")"
		return s
	
	@staticmethod
	def parse(
			source,
			precision_required: str | DatePrecision = 'year',
			same_date_sep=False,
			same_time_sep=False,
			allowed_tz_formats: Optional[str | Set[str]] = None,
	) -> 'FuzzyDatetime':
		"""
		日時文字列を解析し、FuzzyDatetimeオブジェクトを生成する。

		Args:
			source (str): 日時文字列。
			precision_required: ('year'|'month'|'day'|'hour'|'minute'|'second', optional): 入力文字列に要求される最小精度。
			same_date_sep (bool, optional): Trueを指定した場合、日付の区切り文字に同一の記号を要求します。
			same_time_sep (bool, optional): Trueを指定した場合、時間の区切り文字に同一の記号を要求します。
			allowed_tz_formats (Set[str], optional): 許容するタイムゾーン形式の集合。Noneの場合は全てのフォーマットを許可する。
				- 'none': タイムゾーンなし。
				- 'name': タイムゾーン名形式。例: 'Asia/Tokyo', 'America/New_York' など。
				- 'abbr': タイムゾーン略称形式。例: 'JST', 'UTC' など。
				- '+hh:mm':	UTCオフセット拡張形式（コロン区切り）。例: '+09:00', '-05:00' など。
				- '+hhmm': UTCオフセット形式。例: '+0900', '-0500' など。
				- 'utc+hh:mm': 接頭辞付きUTCオフセット拡張形式（コロン区切り）。例: 'UTC+09:00' など。
				- 'utc+hhmm': 接頭辞付きUTCオフセット形式。例: 'UTC+0900' など。
				- 'z': 'Z'形式。UTCを表す。

		Returns:
			FuzzyDatetime: 正規化された日付時刻文字列。
		"""
		if allowed_tz_formats is None:
			allowed_tz_formats = { 'none', 'name', 'abbr', 'z', '+hh:mm', '+hhmm', 'utc+hh:mm', 'utc+hhmm' }
		elif isinstance(allowed_tz_formats, str):
			allowed_tz_formats = set([allowed_tz_formats])
		else:
			allowed_tz_formats = set(allowed_tz_formats)
		
		m = DATETIME_REG.match(source)
		if not m:
			raise FDFormatError(f"Invalid datetime format: \"{source}\"", details={ 'input': source })
		g = m.groupdict()
		
		# 入力の日時精度の特定
		in_precision = DatePrecision.SECOND
		for prec in DatePrecision.slice(DatePrecision.MONTH, None):
			if g[prec.name.lower()] is None:
				in_precision = DatePrecision(prec - 1)
				break
		
		# 要求精度に対する検証
		if precision_required:
			if isinstance(precision_required, str):
				try:
					precision_required = DatePrecision.by_name(precision_required)
				except KeyError as e:
					raise FDValueError(f"Unknown precision has been specified as precision_required: {precision_required}", details={ 'input': source, 'precision_required': precision_required }) from e
			
			if in_precision < precision_required:
				# 入力文字列が要求される日時精度を満たしていない場合
				raise FDPrecisionError(f"Precision not met ({precision_required}) for \"{source}\"", details={ 'input': source, 'precision_required': precision_required })
		
		# 区切り記号の検証
		if same_date_sep and g.get('sep1') and g.get('sep2') and g['sep1'] != g['sep2']:
			raise FDFormatError(f"Mixed date separators in \"{source}\". Use same_date_sep=False to allow mixed separators.", details={ 'input': source, 'sep1': g['sep1'], 'sep2': g['sep2'] })
		if same_time_sep and g.get('sep3') and g.get('sep4') and g['sep3'] != g['sep4']:
			raise FDFormatError(f"Mixed time separators in \"{source}\". Use same_time_sep=False to allow mixed separators.", details={ 'input': source, 'sep3': g['sep3'], 'sep4': g['sep4'] })
		
		# 数値に変換
		year = int(g['year'])
		month = int(g['month']) if g['month'] else None
		day = int(g['day']) if g['day'] else None
		hour = int(g['hour']) if g['hour'] else None
		minute = int(g['minute']) if g['minute'] else None
		second = int(g['second']) if g['second'] else None
		
		# タイムゾーンの検証
		tz_info = None
		if tz_str := g.get('tz'):
			try:
				tz_info = FlexiTimezone.parse(tz_str, allowed_tz_formats)
			except FDTimezoneFormatError as e:
				raise FDTimezoneFormatError(f"Invalid timezone format: \"{g['tz']}\"", details={ 'input': source, 'timezone': g['tz'] }) from e
		elif 'none' not in allowed_tz_formats:
			raise FDTimezoneFormatError(f"Missing timezone in \"{source}\". Add 'none' in tz_formats to allow no timezone.", details={ 'input': source })
		
		return FuzzyDatetime(
			year=year, month=month, day=day,
			hour=hour, minute=minute, second=second,
			tzinfo=tz_info,
			precision=in_precision,
		)
	
	@staticmethod
	def parse_date(
			source,
			precision_required: str | DatePrecision = 'year',
			same_date_sep=False
	) -> 'FuzzyDatetime':
		"""
		日付文字列を解析し、FuzzyDatetimeオブジェクトを生成する。
		
		Args:
			source (str): 日付文字列。
			precision_required: ('year'|'month'|'day', optional): 入力文字列に要求される最小精度。
			same_date_sep (bool, optional): Trueを指定した場合、日付の区切り文字に同一の記号を要求します。

		Returns:
			FuzzyDatetime: 解析された日付オブジェクト。
		"""
		m = DATE_REG.match(source)
		if not m:
			raise FDFormatError(f"Invalid date format: \"{source}\"", details={ 'input': source })
		g = m.groupdict()
		
		# 入力の日時精度の特定
		in_precision = DatePrecision.DAY
		for p in DatePrecision.slice(DatePrecision.MONTH, DatePrecision.HOUR):
			if g[p.name.lower()] is None:
				in_precision = DatePrecision(p - 1)
				break
		
		# 要求精度に対する検証
		if precision_required:
			if isinstance(precision_required, str):
				try:
					precision_required = DatePrecision.by_name(precision_required)
				except KeyError as e:
					raise FDValueError(
						f"Unknown precision has been specified as precision_required: {precision_required}",
						details={ 'input': source, 'precision_required': precision_required }
					) from e
			
			if precision_required > DatePrecision.DAY:
				raise FDPrecisionError(
					f"Argument precision_required must be 'year', 'month', or 'day' for parsing date, but given '{precision_required}'",
					details={ 'input': source, 'precision_required': precision_required }
				)
			
			if in_precision < precision_required:
				raise FDPrecisionError(f"Precision not met ({precision_required}) for \"{source}\"", details={ 'input': source, 'precision_required': precision_required })
		
		# 区切り記号の検証
		if same_date_sep and g.get('sep1') and g.get('sep2') and g['sep1'] != g['sep2']:
			raise FDFormatError(
				f"Mixed date separators in \"{source}\". Use same_date_sep=False to allow mixed separators.",
				details={ 'input': source, 'sep1': g['sep1'], 'sep2': g['sep2'] }
			)
		
		# 数値に変換
		year = int(g['year'])
		month = int(g['month']) if g['month'] else None
		day = int(g['day']) if g['day'] else None
		
		return FuzzyDatetime(
			year=year, month=month, day=day,
			precision=in_precision,
		)
	
	@staticmethod
	def from_datetime(dt: datetime | date):
		"""
		標準の datetime または date オブジェクトから FuzzyDatetime オブジェクトを生成する。
		
		Args:
			dt (datetime | date): datetime または date オブジェクト。

		Returns:
			FuzzyDatetime: 変換された FuzzyDatetime オブジェクト。
		"""
		if isinstance(dt, datetime):
			return FuzzyDatetime(
				year=dt.year, month=dt.month, day=dt.day,
				hour=dt.hour, minute=dt.minute, second=dt.second,
				tzinfo=FlexiTimezone.from_datetime(dt),
				precision=DatePrecision.SECOND
			)
		elif isinstance(dt, date):
			return FuzzyDatetime(
				year=dt.year, month=dt.month, day=dt.day,
				precision=DatePrecision.DAY
			)
		else:
			raise FDTypeError(f"Unsupported type for conversion: {type(dt)}", details={ 'input': dt })
	
	def replace(self, **kwargs):
		"""
		指定されたキーワード引数で日時の一部を置き換えた新しいFuzzyDatetimeオブジェクトを返す。
		
		Args:
			**kwargs: 置き換える日時の要素を指定するキーワード引数。
				- year (int): 年。
				- month (int, optional): 月。
				- day (int, optional): 日。
				- hour (int, optional): 時。
				- minute (int, optional): 分。
				- second (int, optional): 秒。
				- tzinfo (FlexiTimezone, optional): タイムゾーン情報。

		Returns:

		"""
		return FuzzyDatetime(
			year=kwargs.get('year', self.year),
			month=kwargs.get('month', self.month),
			day=kwargs.get('day', self.day),
			hour=kwargs.get('hour', self.hour),
			minute=kwargs.get('minute', self.minute),
			second=kwargs.get('second', self.second),
			tzinfo=kwargs.get('tzinfo', self._tzinfo),
		)
	
	def with_precision(
			self,
			precision: str | DatePrecision,
			default: Optional[datetime] = None,
			rounding='trunc',
	) -> 'FuzzyDatetime':
		"""
		日時を指定された精度に調整した新たなFuzzyDatetimeオブジェクトを返します。
		精度が不足している場合は、指定されたデフォルト値で補完されます。
		指定された精度が現在よりも低くなる場合、不必要な部分が切り落とされます。
		rounding 引数により、端数処理の方法を指定できます。

		Args:
			precision (str | DatePrecision): 目標とする精度。
			default (datetime, optional): 精度が不足している場合のデフォルト値。Noneの場合は規定値で補完されます。
			rounding (str, optional): 端数処理の方法。precision が年または月の場合、'trunc' のみが許容されます。
				- 'trunc': 切り捨て。
				- 'ceil': 切り上げ。
				- 'round': 四捨五入。

		Returns:
			FuzzyDatetime: 指定された精度に調整された新しいFuzzyDatetimeオブジェクト。
		"""
		if isinstance(precision, str):
			try:
				prec = DatePrecision.by_name(precision)
			except KeyError as e:
				raise FDValueError(f"Unknown precision: {precision}", details={ 'input': precision }) from e
		else:
			prec = precision
		
		if prec == self._precision:
			# 現在の精度と同じ場合はそのまま返す
			return self
		elif prec < self._precision:
			# 現在の精度が指定された精度より高い場合、必要な部分を削除
			if rounding == 'trunc':
				# 切り捨て
				components = [*self._components[:prec + 1]]
			elif rounding in ('ceil', 'round'):
				if prec < DatePrecision.DAY:
					# 年または月の精度で切り上げ・四捨五入は許可されない
					raise FDValueError(f"Rounding method '{rounding}' is not defined for precision {prec}", details={ 'rounding': rounding, 'precision': prec })
				
				if rounding == 'ceil':
					# 切り上げ
					components = (
						*self._components[:prec],
						self._components[prec] + 1 if self._components[prec + 1] > 0 else self._components[prec]
					)
				else:
					# 四捨五入
					width = 24 if prec == DatePrecision.DAY else 60
					components = (
						*self._components[:prec],
						self._components[prec] + 1 if self._components[prec + 1] >= width / 2 else self._components[prec]
					)
			else:
				raise FDValueError(f"Unknown rounding method: '{rounding}'", details={ 'rounding': rounding })
		else:
			# 現在の精度が指定された精度より低い場合、必要な部分を規定値で埋める
			if default is None:
				default = datetime(self.year, 1, 1, 0, 0, 0)
			
			components = (
				default.year if self.year is None else self.year,
				default.month if self.month is None else self.month,
				default.day if self.day is None else self.day,
				default.hour if self.hour is None else self.hour,
				default.minute if self.minute is None else self.minute,
				default.second if self.second is None else self.second,
			)[:prec + 1]
		
		if prec < DatePrecision.HOUR:
			tzinfo = None
		elif default.tzinfo:
			if not isinstance(default.tzinfo, FlexiTimezone):
				# タイムゾーン情報が FlexiTimezone でない場合はエラーを送出する
				raise FDTypeError(f"FlexiTimezone expected for default.tzinfo, but got {type(default.tzinfo)}", details={ 'default': default })
			tzinfo = default.tzinfo
		else:
			tzinfo = self._tzinfo
		
		return FuzzyDatetime(
			*components,
			tzinfo=tzinfo,
			precision=prec,
		)
	
	def ensure_timezone(self, default_tz: str | FlexiTimezone):
		"""
		指定されたタイムゾーンを適用する。タイムゾーンが既に設定されている場合、変更は適用されません。

		Args:
			default_tz (str | FlexiTimezone): タイムゾーンが指定されていない場合に適用するデフォルトのタイムゾーン。
		Returns:
			FuzzyDatetime: タイムゾーンが適用された新しいFuzzyDatetimeオブジェクト。
		"""
		if self._tzinfo:
			return self
		elif isinstance(default_tz, str):
			default_tz = FlexiTimezone.parse(default_tz)
		
		return FuzzyDatetime(
			year=self.year, month=self.month, day=self.day,
			hour=self.hour, minute=self.minute, second=self.second,
			tzinfo=default_tz,
			precision=self._precision,
		)
	
	def strftime(self,
			format: str = '%Y/%m/%d %H:%M:%S %z',
			tz_formats: Sequence[str] = ('abbr', '+hh:mm'),
	) -> str:
		"""
		日時を指定されたフォーマットで文字列に変換する。

		Args:
			format (str, optional): フォーマット文字列。
				使用可能な形式・プレースホルダは datetime.datetime.strftime を参照してください。
				追加プレースホルダ:
					- '%@': tz_formats に従い適切な形式のタイムゾーンを選んで挿入します。タイムゾーン情報が存在しない場合は空白文字列で置換されます。
			tz_formats (Sequence[str], optional): タイムゾーンの書式。フォーマット文字列に '%@' が含まれる場合に使用されます。
				自身にタイムゾーン情報が存在する場合にのみ、指定された順にタイムゾーン形式の適用を試みます。
				- 'name': タイムゾーン名形式。例: 'Asia/Tokyo', 'America/New_York' など。
				- 'abbr': タイムゾーン略称形式。例: 'JST', 'UTC' など。
				- '+hh:mm':	UTCオフセット拡張形式（コロン区切り）。例: '+09:00', '-05:00' など。
				- '+hhmm': UTCオフセット形式。例: '+0900', '-0500' など。
				- 'utc+hh:mm': 接頭辞付きUTCオフセット拡張形式（コロン区切り）。例: 'UTC+09:00' など。
				- 'utc+hhmm': 接頭辞付きUTCオフセット形式。例: 'UTC+0900' など。

		Returns:
			str: フォーマットされた日時文字列。
		"""
		dt = self.to_datetime()
		if tz := self._tzinfo:
			format = format.replace('%@', tz.try_format(tz_formats))  # カスタム書式タイムゾーン
		else:
			format = format.replace('%@', '')  # カスタム書式タイムゾーン
		
		return dt.strftime(format)
	
	def to_string(self,
			zero_pad=True,
			date_sep='/',
			time_sep=':',
			tz_formats: Optional[str | Sequence[str]] = ('abbr', 'name', '+hhmm'),
	):
		"""
		日付時刻文字列を一貫した形式に整形します。
		得られる文字列の書式は format メソッドにおける '%Y/%m/%d %H:%M:%S %@' と類似していますが、
		format メソッドとは異なり精度に合わせて出力される位が変化します。

		Args:
			zero_pad (bool, optional): 月、日、時、分、秒をゼロパディングするかどうか。
			date_sep (str, optional): 日付の区切り文字。規定値は '/'。
			time_sep (str, optional): 時刻の区切り文字。規定値は ':'。
			tz_formats (str | Sequence[str], optional): タイムゾーン形式の優先順序。自身にタイムゾーン情報が存在する場合、指定された順にタイムゾーン形式の適用を試みる。
				- 'name': タイムゾーン名形式。例: 'Asia/Tokyo', 'America/New_York' など。
				- 'abbr': タイムゾーン略称形式。例: 'JST', 'UTC' など。
				- '+hh:mm':	UTCオフセット拡張形式（コロン区切り）。例: '+09:00', '-05:00' など。
				- '+hhmm': UTCオフセット形式。例: '+0900', '-0500' など。
				- 'utc+hh:mm': 接頭辞付きUTCオフセット拡張形式（コロン区切り）。例: 'UTC+09:00' など。
				- 'utc+hhmm': 接頭辞付きUTCオフセット形式。例: 'UTC+0900' など。

		Returns:
			 str: 正規化された日付時刻文字列。
		"""
		# 文字列組み立て
		out = _pad(self.year, 4) if zero_pad else str(self.year)
		component_configs = [
			(self.month, date_sep),
			(self.day, date_sep),
			(self.hour, ' '),
			(self.minute, time_sep),
			(self.second, time_sep),
		]
		for component, sep in component_configs[:self._precision]:
			out += sep + (_pad(component, 2) if zero_pad else str(component))
		
		# タイムゾーン
		if self._tzinfo and (tz_str := self._tzinfo.try_format(tz_formats)):
			out += ' ' + tz_str
		
		return out
	
	def to_date(self, default: date = None) -> date:
		"""
		FuzzyDatetimeオブジェクトをdateオブジェクトに変換する。
		
		Returns:
			date: 日付オブジェクト。
		"""
		if default is None:
			def_components = (1, 1)
		else:
			def_components = (default.month, default.day)
		
		precision = self._precision if self._precision < DatePrecision.DAY else DatePrecision.DAY
		return date(
			*self._components[:precision + 1],
			*def_components[precision:]
		)
	
	def to_datetime(self, default: datetime = None) -> datetime:
		"""
		FuzzyDatetimeオブジェクトをdatetimeオブジェクトに変換する。
		
		Returns:
			datetime: 日時オブジェクト。
		"""
		tz = self._tzinfo
		
		if default is None:
			def_components = (1, 1, 0, 0, 0)
		else:
			def_components = (default.month, default.day, default.hour, default.minute, default.second)
		
		return datetime(
			*self._components[:self._precision + 1],
			*def_components[self._precision:],
			tzinfo=tz
		)
	
	def to_isoformat(self, sep='T', timespec='auto') -> str:
		"""
		FuzzyDatetimeオブジェクトをISO 8601形式の文字列に変換する。

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
		FuzzyDatetimeオブジェクトの文字列表現を返す。
		
		Returns:
			str: 日時の文字列表現。
		"""
		return self.to_string(
			zero_pad=True,
			date_sep='/',
			time_sep=':',
			tz_formats=('abbr', 'name', '+hh:mm')
		)
	
	def __eq__(self, other):
		"""
		FuzzyDatetimeオブジェクトの等価性を比較する。
		
		Args:
			other (object): 比較対象のオブジェクト。
		
		Returns:
			bool: 等価であればTrue、そうでなければFalse。
		"""
		if not isinstance(other, FuzzyDatetime):
			return NotImplemented
		return (
				self.precision == other.precision
				and self._components == other._components
				and self._tzinfo == other._tzinfo
		)
	
	def __hash__(self):
		"""
		FuzzyDatetimeオブジェクトのハッシュ値を返す。
		
		Returns:
			int: ハッシュ値。
		"""
		return hash((self.precision, self._components, self._tzinfo))
	
	def __add__(self, other):
		"""
		FuzzyDatetimeオブジェクトにtimedeltaを加算する。

		Args:
			other (timedelta): 加算する時間差。

		Returns:
			FuzzyDatetime: 加算後の新しいFuzzyDatetimeオブジェクト。
		"""
		if not isinstance(other, timedelta):
			return NotImplemented
		
		dt = self.to_datetime() + other
		components = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)[:self._precision + 1]
		
		return FuzzyDatetime(
			*components,
			tzinfo=self._tzinfo,
			precision=self._precision,
		)
	
	def __sub__(self, other):
		"""
		FuzzyDatetimeオブジェクトにtimedeltaを減算する。

		Args:
			other (timedelta): 加算する時間差。

		Returns:
			FuzzyDatetime: 加算後の新しいFuzzyDatetimeオブジェクト。
		"""
		if not isinstance(other, timedelta):
			return NotImplemented
		
		dt = self.to_datetime() - other
		components = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)[:self._precision + 1]
		
		return FuzzyDatetime(
			*components,
			tzinfo=self._tzinfo,
			precision=self._precision,
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
