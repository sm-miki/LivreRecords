from typing import Optional
from abc import ABCMeta, abstractmethod
import numpy as np
import cv2
import PIL
from PIL import Image, ImageDraw
from PIL.Image import Image as PILImage

from .img_utils import pil2cv, cv2pil, get_font
from .image_correction import crop_receipt, closing, gamma_correction, greyscale, unsharp_masking

class OCRTextBlock:
	def __init__(self,
			text: str,
			bbox: tuple[tuple[float, float], ...],
			prob: float
	):
		"""OCRによって読み取ったテキストの情報。

		Args:
			bbox:
				文字の位置を表すポリゴンの頂点集合。。
				画像の左上を原点として、各要素はそれぞれ (左上, 右上, 右下, 左下) の座標を表す。
			text: 文字列。
			prob: 読み取りの確信度。0.0 から 1.0 の範囲の値をとる。
		"""
		self.bbox: tuple[tuple[float, float], ...] = bbox
		self.text = text
		self.prob = prob

class OCRResult:
	def __init__(
			self,
			ocr_engine: 'BaseOCREngine',
			original_image: np.ndarray,
			image: np.ndarray,
			texts: list[OCRTextBlock],
	):
		self.ocr_engine = ocr_engine
		self.original_image = original_image
		self.image = image
		self.texts = texts

class BaseOCREngine(metaclass=ABCMeta):
	@abstractmethod
	def recognize_text(
			self, image: PILImage | np.ndarray
	) -> list[OCRTextBlock]:
		"""OCRを使って指定された画像から文字列とその位置情報を抽出します。
		
		Args:
			image: 読み取り対象の画像。

		Returns:
			画像から読み取ったすべてのテキスト情報を保持するリスト。
		"""
		pass
	
	def render_text_blocks(self,
			image: PILImage | np.ndarray,
			text_list: list[OCRTextBlock],
			font_path: Optional[str] = None
	) -> PILImage | np.ndarray:
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
		
		for block in text_list:
			tl, tr, br, bl = block.bbox
			height = (bl[1] - tl[1] + br[1] - tr[1]) // 2
			
			# ポリゴンの描画
			vertices = tuple(map(tuple, (tl, tr, br, bl)))
			draw.polygon(vertices, outline=(0, 255, 0), width=2)  # 緑色の線
			
			# フォントの決定
			font = get_font(font_path, size=self.get_font_size(height))
			
			# テキストの描画（オプション）
			text_x = tl[0]
			text_y = tl[1] - d if tl[1] - d > 0 else tl[1] + d
			draw.text((text_x, text_y), block.text, fill=(255, 17, 102), font=font)
		
		return pil2cv(image) if cv_format else image
	
	@staticmethod
	def get_font_size(height: float) -> int:
		"""指定されたテキストブロックを描画するための適度な文字サイズを取得する。

		Args:
			height: テキストブロックの平均高さ。

		Returns:
			フォントサイズ。
		"""
		return max(1, int(height * 0.6))
	
	def preprocess(
			self,
			image: np.ndarray,
			preprocess_types: Optional[str | tuple[str]] = None
	) -> np.ndarray:
		"""画像の前処理
		
		Args:
			image:
			preprocess_types:

		Returns:

		"""
		
		if isinstance(preprocess_types, str):
			preprocess_options = { preprocess_types: { } }
		elif isinstance(preprocess_types, (list, tuple)):
			preprocess_options = dict([
				(s[0], s[1]) if isinstance(s, (list, tuple)) else (s, { })
				for s in preprocess_types or []
			])
		else:
			raise TypeError(f"`preprocess_types` must be str of preprocess type name, or collection of (type, option), but given {type(preprocess_types)}.")
		
		if 'crop' in preprocess_options:
			kwargs = preprocess_options['crop']
			image = crop_receipt(image, **kwargs)
		
		if 'closing' in preprocess_options:
			# 収縮処理（わずかに）
			kwargs = preprocess_options['closing']
			image = closing(image, **kwargs)
		
		if 'greyscale' in preprocess_options:
			kwargs = preprocess_options['greyscale']
			image = greyscale(image, **kwargs)
		
		if 'gamma_correction' in preprocess_options:
			kwargs = preprocess_options['gamma_correction']
			image = gamma_correction(image, **kwargs)
		
		if 'unsharp_masking' in preprocess_options:
			kwargs = preprocess_options['unsharp_masking']
			image = unsharp_masking(image, **kwargs)
		
		return cv2.cvtColor(image.clip(0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
	
	def recognize(self,
			image, preprocess_type: Optional[str | tuple[str]] = None
	) -> OCRResult:
		"""
		
		Args:
			image (numpy.ndarray):
			preprocess_type:

		Returns:

		"""
		original = image.copy()
		image = self.preprocess(image, preprocess_type)  # データの前処理 (処理内容は設定による)
		
		texts: list[OCRTextBlock] = self.recognize_text(image)  # 文字の読み取り
		
		return OCRResult(self, original, image, texts)

OCREngine = BaseOCREngine

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
