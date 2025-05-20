from collections import deque
from typing import Union
import cv2
import numpy as np
import re
from PIL import Image, ImageDraw, ImageFont

from ocr_engine.img_utils import cv2pil, pil2cv
from ocr_engine.base_ocr_engine import BaseOCREngine, OCRTextBlock, OCRResult

class OCRTextDetail:
	def __init__(self, text_box: OCRTextBlock, center, size):
		self.bbox = text_box.bbox
		self.text = text_box.text
		self.prob = text_box.prob
		self.center = center
		self.size = size
	
	@property
	def width(self):
		return self.size[0]
	
	@property
	def height(self):
		return self.size[1]
	
	@property
	def center_x(self):
		return self.center[0]
	
	@property
	def center_y(self):
		return self.center[1]
	
	@property
	def left(self) -> float:
		return (self.bbox[0][0] + self.bbox[3][0]) / 2
	
	@property
	def right(self) -> float:
		return (self.bbox[1][0] + self.bbox[2][0]) / 2
	
	@property
	def top(self) -> float:
		return (self.bbox[0][1] + self.bbox[1][1]) / 2
	
	@property
	def bottom(self) -> float:
		return (self.bbox[2][1] + self.bbox[3][1]) / 2
	
	def __repr__(self):
		return (
			f"{self.__class__.__name__}(bbox={self.bbox}, "
			f"text='{self.text}', "
			f"center={self.center}, "
			f"size={self.size})"
		)

class ReadResult:
	def __init__(self,
			ocr_result: OCRResult,
			lines: list[list[OCRTextDetail]],
			receipt_data: dict,
	):
		self.ocr_result = ocr_result
		self.lines = lines
		self.receipt_data = receipt_data
	
	def render_text_overlay(
			self, /,
			font_path: Union[str | None] = None,
			border_color1=(0, 255, 0),
			border_color2=(0, 51, 255),
			text_color=(255, 17, 102),
	):
		"""
		OCRにより読み取った文字列を画像上に描画して返す。

		Args:
			text_color: 文字列の描画色。
			border_color: 文字列の検出位置を示す枠線の描画色。
			font_path: フォントのパス。None を指定した場合は自動的に選ばれる。

		Returns (np.ndarray):
			読み取った文字列を描画した画像。
		"""
		if font_path is None:
			font_path = r"C:\Windows\Fonts\msgothic.ttc"
		
		image = cv2pil(self.ocr_result.image)
		
		# PillowのImageDrawオブジェクトを作成
		draw = ImageDraw.Draw(image)
		img_px = min(image.width, image.height)  # 画像の大きさの基準値
		offset_y = img_px * 0.01  # バウンディングボックスの左上点を基準とする、テキストの描画位置の上下オフセット
		
		border_colors = [border_color1, border_color2]
		
		for i, line in enumerate(self.lines):
			for block in line:
				tl, tr, br, bl = block.bbox
				height = (bl[1] - tl[1] + br[1] - tr[1]) // 2
				
				# 矩形の描画
				draw.polygon(tuple(map(tuple, (tl, tr, br, bl))), outline=border_colors[i % 2], width=2)  # 緑色の線
				
				# フォントの決定
				font = get_font(font_path, size=max(1, int(height * 0.6)))
				
				# テキストの描画（オプション）
				text_x = tl[0]
				text_y = tl[1] - offset_y if tl[1] - offset_y > 0 else tl[1] + offset_y
				draw.text((text_x, text_y), block.text, fill=text_color, font=font)
		
		return pil2cv(image)

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

class ReceiptReader:
	def __init__(self, ocr_engine: BaseOCREngine):
		self.ocr_engine = ocr_engine
		self.isbn_reg = re.compile(r"(^|[ :;,])(?P<isbn>978(\d){10})(?=[ :;,]|$)")
	
	def recognize(self,
			image_path: str,
			preprocess_type: Union[str | list[str] | list[tuple[str, dict]] | None] = None
	):
		"""画像から文字を読み取る"""
		ocr_result: OCRResult = self.ocr_engine.recognize(image_path, preprocess_type)
		
		# 文字列を行ごとにグループ分け
		lines = self.group_by_line(ocr_result.texts)
		
		receipt_data = self.parse_receipt_data(lines)
		
		return ReadResult(ocr_result=ocr_result, lines=lines, receipt_data=receipt_data)
	
	def group_by_line(
			self, text_blocks: list[OCRTextBlock],
			y_thresh_ratio=0.3,
			gap_thresh_ratio=1.0,
			space_ratio=0.5,
	):
		"""
		読み取った文字を行ごとにグループ分けする
	
		Args:
			text_blocks:
			y_thresh_ratio: 2つの文字列を同一行とみなすためのY軸方向間隔の閾値（文字列高さを1とする比率）。
			gap_thresh_ratio: 2つの文字列を結合するためのX軸方向間隔の閾値（1文字幅を1とする比率）。
			space_ratio: 隣接する文字列の結合時にスペースを挿入するかどうか判定するためのX軸方向間隔の閾値（1文字幅を1とする比率）。

		Returns:

		"""
		# size: [n, 4, 2]
		order = np.argsort([bbox[0][0] + bbox[3][0] for bbox in map(lambda block: block.bbox, text_blocks)])
		
		sorted_blocks = [text_blocks[i] for i in order]
		bboxes = np.array([text_blocks[i].bbox for i in order])
		
		left = (bboxes[:, 0, 0] + bboxes[:, 3, 0]) / 2
		right = (bboxes[:, 1, 0] + bboxes[:, 2, 0]) / 2
		top = (bboxes[:, 0, 1] + bboxes[:, 1, 1]) / 2
		bottom = (bboxes[:, 2, 1] + bboxes[:, 3, 1]) / 2
		
		# 各四角形の中心座標を求める
		center_x = (left + right) / 2
		center_y = (top + bottom) / 2
		
		# 各四角形の軸方向の大きさを求める
		width = right - left
		height = bottom - top
		
		char_widths = width / [len(block.text) for block in sorted_blocks]
		
		sorted_blocks = [
			OCRTextDetail(block, (x, y), (w, h))
			for block, x, y, w, h in zip(sorted_blocks, center_x, center_y, width, height)
		]
		
		boxes_in_line: list[deque[int]] = []  # 各行に属するブロックのインデックス列の列
		last_blocks: deque[int] = deque()  # 各行の末尾に位置する文字列ボックスのインデックス列
		
		# 最初の文字列ボックスを登録
		boxes_in_line.append(deque([0]))
		last_blocks.append(0)
		
		for i, block in enumerate(sorted_blocks[1:], start=1):
			gap_y = np.abs(center_y[last_blocks] - block.center_y)  # size: [num_lines]
			nearest_line = np.argmin(gap_y)
			if min(height[last_blocks[nearest_line]], block.height) * y_thresh_ratio < gap_y[nearest_line]:
				# 分類先の行グループが見つからなかった
				boxes_in_line.append(deque([i]))
				last_blocks.append(i)
			else:
				# 分類先の行グループが見つかった
				prev_idx = last_blocks[nearest_line]
				prev_block = sorted_blocks[prev_idx]
				
				### 直前のボックスに対して距離が近い場合はボックスを統合する ###
				gap_x = (block.left - prev_block.right) / gap_thresh_ratio
				if char_widths[prev_idx] < gap_x and char_widths[prev_idx] < gap_x:
					# 直前のブロックと十分に離れている => 独立したブロックとして登録する
					boxes_in_line[nearest_line].append(i)
					last_blocks[nearest_line] = i
				else:
					# 直前のブロックと近い => ブロックを結合する
					gap_x /= space_ratio
					if char_widths[prev_idx] < gap_x and char_widths[prev_idx] < gap_x:
						# 間隔が (1文字幅 * space_ratio) 以上の場合 => スペースを挿入する
						new_text = prev_block.text + ' ' + block.text
					else:
						# 間隔が (1文字幅 * space_ratio) 以下の場合 => スペースを挿入しない
						new_text = prev_block.text + block.text
					
					new_prob = (prev_block.prob + block.prob) / 2
					new_bbox = (prev_block.bbox[0], block.bbox[1], block.bbox[2], prev_block.bbox[3])
					new_center = (
						(prev_block.left + block.right) / 2,
						(prev_block.top + block.bottom) / 2,
					)
					new_size = (
						block.right - prev_block.left,
						block.bottom - prev_block.top,
					)
					center_x[prev_idx], center_y[prev_idx] = new_center
					width[prev_idx], height[prev_idx] = new_size
					char_widths[prev_idx] = width[prev_idx] / len(new_text)
					
					# 直前のブロックを結合後のブロックで置換
					sorted_blocks[prev_idx] = OCRTextDetail(
						OCRTextBlock(new_text, new_bbox, new_prob),
						center=new_center,
						size=new_size
					)
		
		# 行をそのY座標ごとにソートする
		line_order = np.argsort(center_y[last_blocks])
		
		return [[sorted_blocks[i] for i in boxes_in_line[k]] for k in line_order]
	
	def parse_receipt_data(self, lines: list[list[OCRTextDetail]]):
		data = { 'books': [] }
		
		# レシート内の文字領域の最大範囲を特定する
		horizontal_bounds = np.array([(line[-1].left, line[-1].right) for line in lines])
		bound_l = horizontal_bounds[:, 0].min()
		bound_r = horizontal_bounds[:, 1].max()
		
		for line in lines:
			for block in line:
				if m := self.isbn_reg.search(block.text):
					data['books'].append({ 'isbn': m.group('isbn') })
		
		return data
