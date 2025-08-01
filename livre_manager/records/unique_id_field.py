import nanoid
from django.db import models

def generate_nanoid():
	"""
	デフォルトのNanoIDを生成する関数
	"""
	return nanoid.generate()

class NanoIDField(models.CharField):
	"""
	NanoIDをプライマリキーとして使用するためのカスタムフィールド
	"""
	
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 21)
		kwargs.setdefault('unique', True)
		kwargs.setdefault('default', generate_nanoid)
		kwargs.setdefault('editable', False)
		super().__init__(*args, **kwargs)
	
	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		# default, editable, primary_key を常に含める
		if self.default == generate_nanoid:
			kwargs['default'] = generate_nanoid
		if not self.editable:
			kwargs['editable'] = False
		return name, path, args, kwargs
