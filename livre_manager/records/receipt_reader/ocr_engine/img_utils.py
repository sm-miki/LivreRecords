from typing import Union
import numpy as np
import cv2
from PIL import Image, ImageFont

def pil2cv(image):
	""" PIL型 -> OpenCV型 """
	new_image = np.array(image, dtype=np.uint8)
	if new_image.ndim == 2:  # モノクロ
		pass
	elif new_image.shape[2] == 3:  # カラー
		new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
	elif new_image.shape[2] == 4:  # 透過
		new_image = cv2.cvtColor(new_image, cv2.COLOR_RGBA2BGRA)
	return new_image

def cv2pil(image):
	""" OpenCV型 -> PIL型 """
	new_image = image.copy()
	if new_image.ndim == 2:  # モノクロ
		pass
	elif new_image.shape[2] == 3:  # カラー
		new_image = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
	elif new_image.shape[2] == 4:  # 透過
		new_image = cv2.cvtColor(new_image, cv2.COLOR_BGRA2RGBA)
	new_image = Image.fromarray(new_image)
	return new_image

def get_font(
		font_path: Union[str | None] = None,
		size=10
) -> ImageFont:
	try:
		if font_path:
			font = ImageFont.truetype(font_path, size)  # フォントパスとサイズを指定
		else:
			# デフォルトフォントを試す（日本語が表示できるかは環境による）
			font = ImageFont.load_default()
			print("警告: フォントパスが指定されていません。デフォルトフォントを使用します。日本語が正しく表示されない可能性があります。")
	except IOError:
		print("警告: 指定されたフォントファイルが見つかりませんでした。デフォルトフォントを使用します。日本語が正しく表示されない可能性があります。")
		font = ImageFont.load_default()
	
	return font
