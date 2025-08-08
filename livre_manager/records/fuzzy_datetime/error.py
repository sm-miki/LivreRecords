"""
fuzzy_datetime.error
日時関連のカスタムエラークラスを定義する。
"""

class FDError(Exception):
	"""
	日時関連のエラーを表す基底カスタムエラークラス。
	"""
	
	def __init__(self, message, code='UNKNOWN_ERROR', details=None):
		super().__init__(message)
		self.code = code
		self.details = details if details is not None else { }
		
class FDFormatError(ValueError, FDError):
	"""
	書式が不正な場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'FORMAT_ERROR', details)

class FDValueError(ValueError, FDError):
	"""
	値が範囲外の場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'VALUE_ERROR', details)

class FDPrecisionError(ValueError, FDError):
	"""
	精度の不整合に関するエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'PRECISION_ERROR', details)

class FDTimezoneFormatError(ValueError, FDError):
	"""
	タイムゾーンのパースに失敗した場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'TIMEZONE_PARSE_ERROR', details)
		
class FDTimezoneValueError(ValueError, FDError):
	"""
	タイムゾーンの値が不正な場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'TIMEZONE_VALUE_ERROR', details)

class FDTypeError(TypeError, FDError):
	"""
	型が不正な場合のエラー。
	"""
	
	def __init__(self, message, details=None):
		super().__init__(message, 'TYPE_ERROR', details)
