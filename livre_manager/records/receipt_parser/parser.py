from .reader import TextReader

class ReceiptParser:
	def __init__(self):
		self.reader = TextReader(lang_list=['en', 'ja'])
		
		
	def parse_from_image(self, image_path):
		texts = self.reader.recognize(image_path)
		
		raise NotImplementedError()