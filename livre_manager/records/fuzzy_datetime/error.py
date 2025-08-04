"""
fuzzy_datetime.error
日時関連のカスタムエラークラスを定義する。
"""

class FuzzyDatetimeError(Exception):
	"""
	日時関連のエラーを表す基底カスタムエラークラス。
	"""
	
	def __init__(self, message, code='UNKNOWN_ERROR', details=None):
		super().__init__(message)
		self.name = 'DateTimeError'
		self.code = code
		self.details = details if details is not None else { }

class FDInvalidFormatError(FuzzyDatetimeError):
	"""
	書式が不正な場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'INVALID_FORMAT', details)
		self.name = 'InvalidFormatError'

class FDInvalidValueError(FuzzyDatetimeError):
	"""
	値が範囲外の場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'INVALID_VALUE', details)
		self.name = 'InvalidValueError'

class FDPrecisionError(FuzzyDatetimeError):
	"""
	精度が不足している場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'PRECISION_NOT_MET', details)
		self.name = 'PrecisionError'

class FDInvalidTimezoneError(FuzzyDatetimeError):
	"""
	タイムゾーンが不正な場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'INVALID_TIMEZONE', details)
		self.name = 'InvalidTimezoneError'
