import numpy as np
from PIL import Image
import easyocr

class TextReader:
	def __init__(self, lang_list=None, link_threshold=0.3, max_image_size=2048, gpu=False):
		self.max_image_size = max_image_size
		self.link_threshold = link_threshold
		self.lang_list = lang_list or ['en', 'ja']
		self.reader = easyocr.Reader(lang_list, gpu=gpu)
	
	def recognize(self, image_path):
		"""画像から文字を読み取る"""
		img = Image.open(image_path)
		result = self.reader.readtext(img, link_threshold=self.link_threshold)
		
		return result
