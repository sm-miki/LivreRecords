from typing import Union
from abc import ABCMeta, abstractmethod
import numpy as np
import cv2
import PIL
from PIL import Image, ImageDraw
import time

from .img_utils import pil2cv, cv2pil, get_font
from .crop import crop_receipt

class OCRTextBox:
	def __init__(self,
			vertices: tuple[tuple[float, float], ...],
			text: str,
			prob: float
	):
		"""OCRによって読み取ったテキストの情報。

		Args:
			vertices:
				文字の位置を表すポリゴンの頂点集合。。
				画像の左上を原点として、各要素はそれぞれ (左上, 右上, 右下, 左下) の座標を表す。
			text: 文字列。
			prob: 読み取りの確信度。0.0 から 1.0 の範囲の値をとる。
		"""
		self.vertices: tuple[tuple[float, float], ...] = vertices
		self.text = text
		self.prob = prob

class BaseOCRReader(metaclass=ABCMeta):
	def __init__(self, preprocess_types=None):
		self.preprocess_types = set(preprocess_types or ())
	
	@abstractmethod
	def recognize_text(
			self, image: Union[PIL.Image | np.ndarray]
	) -> list[OCRTextBox]:
		"""OCRを使って指定された画像から文字列とその位置情報を抽出します。
		
		Args:
			image: 読み取り対象の画像。

		Returns:
			画像から読み取ったすべてのテキスト情報を保持するリスト。
		"""
		pass
	
	@staticmethod
	def get_font_size(height: float) -> int:
		"""指定されたテキストボックスを描画するための適度な文字サイズを取得する。
		
		Args:
			height: テキストボックスの平均高さ。

		Returns:
			フォントサイズ。
		"""
		return max(1, int(height * 0.6))
	
	def render_text_boxes(self,
			image: Union[PIL.Image | np.ndarray],
			text_list: list[OCRTextBox],
			font_path: Union[str | None] = None
	) -> Union[PIL.Image | np.ndarray]:
		"""読み取った文字を画像中に描画する。
		
		Args:
			image:
			text_list:
			font_path:

		Returns:

		"""
		cv_format = not isinstance(image, PIL.Image.Image)
		if cv_format:
			image = cv2pil(image)
		
		# PillowのImageDrawオブジェクトを作成
		draw = ImageDraw.Draw(image)
		img_px = min(image.width, image.height)
		d = img_px * 0.01
		
		for box in text_list:
			tl, tr, br, bl = box.vertices
			height = (bl[1] - tl[1] + br[1] - tr[1]) // 2
			
			# ポリゴンの描画
			vertices = tuple(map(tuple, (tl, tr, br, bl)))
			draw.polygon(vertices, outline=(0, 255, 0), width=2)  # 緑色の線
			
			# フォントの決定
			font = get_font(font_path, size=self.get_font_size(height))
			
			# テキストの描画（オプション）
			text_x = tl[0]
			text_y = tl[1] - d if tl[1] - d > 0 else tl[1] + d
			draw.text((text_x, text_y), box.text, fill=(255, 17, 102), font=font)
		
		return pil2cv(image) if cv_format else image
	
	def preprocess(self, image: np.ndarray) -> np.ndarray:
		"""画像の前処理
		
		Args:
			image:

		Returns:

		"""
		"""OCR認識前処理として、文字をわずかに太くする処理"""
		# image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
		# _, image_cv = cv2.threshold(image_cv, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
		
		""" クロージング処理 """
		
		if 'crop' in self.preprocess_types:
			image = crop_receipt(image)
		
		if 'closing' in self.preprocess_types:
			# 収縮処理（わずかに）
			kernel_erode = np.ones((3, 3), np.uint8)
			image = cv2.erode(image, kernel_erode, iterations=1)
			
			# 膨張処理（気持ち大きめに）
			kernel_dilate = np.ones((3, 3), np.uint8)
			image = cv2.dilate(image, kernel_dilate, iterations=1)
		
		return image
	
	def recognize(self, image_path: str):
		img = cv2.imread(image_path)
		img = self.preprocess(img)  # データの前処理 (処理内容は設定による)
		
		boxes = self.recognize_text(img)  # 文字の読み取り
		
		# レシートデータを構造的に解釈する
		self.parse_receipt_data(img, boxes)
		
	def parse_receipt_data(self, image, boxes):
		pass

def order_points(pts):
	"""4点の座標を左上、右上、右下、左下の順に並べ替える"""
	rect = np.zeros((4, 2), dtype="float32")
	s = pts.sum(axis=1)
	rect[0] = pts[np.argmin(s)]  # 左上：x+y最小
	rect[2] = pts[np.argmax(s)]  # 右下：x+y最大
	
	diff = np.diff(pts, axis=1)
	rect[1] = pts[np.argmin(diff)]  # 右上：x-yが最小
	rect[3] = pts[np.argmax(diff)]  # 左下：x-yが最大
	return rect
