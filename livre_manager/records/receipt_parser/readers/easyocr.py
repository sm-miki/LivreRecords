from typing import Union
import os
import numpy as np
import cv2

from base_reader import BaseOCRReader, OCRTextBox

os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2, 30).__str__()
import easyocr

class EasyOCRReader(BaseOCRReader):
	def __init__(
			self,
			preprocess_types: Union[str | tuple[str] | None] = None,
			lang_list: Union[tuple[str] | None] = None,
			link_threshold=0.3,
			max_image_size=2048,
			gpu=False,
	):
		super().__init__(preprocess_types=preprocess_types)
		
		if lang_list is None:
			lang_list = ['en', 'ja']
		self.max_image_size = max_image_size
		self.link_threshold = link_threshold
		self.reader = easyocr.Reader(lang_list, gpu=gpu)
	
	def recognize_text(self, image):
		"""OCRを使って指定された画像から文字列とその位置情報を抽出します。

		Args:
			image (numpy.ndarray): 読み取り対象の画像。

		Returns (list[tuple[tuple, str, float]]):
			画像から読み取ったすべてのテキスト情報を保持するリスト。
			各テキスト情報:
			 - 位置 (tuple[tuple, ..])
			 - 文字列 (str)
			 - 確信度 (float)
		"""
		
		# 画像サイズを制限・縮小する
		size = np.array(image.size[:2])
		rescale = self.max_image_size / size.max()
		if rescale < 1:
			newsize = tuple(size * rescale)
			image = cv2.resize(image, newsize)
		
		result = self.reader.readtext(image, link_threshold=0.3)
		
		return [
			OCRTextBox(
				vertices=tuple((pt[0] / rescale, pt[1] / rescale) for pt in vertices),
				text=text,
				prob=prob)
			for vertices, text, prob in result
		]
