import numpy as np
from pathlib import Path
import traceback

from ocr_engine.easyocr_engine import EasyOCREngine
from reader import ReceiptReader, ReadResult

import cv2

def format_bbox(bbox):
	return ', '.join(f"({int(b[0])}, {int(b[1])})" for b in bbox)

class Tester:
	def __init__(self, outdir=None):
		if outdir is None:
			self.outdir = Path('ocr_out')
		else:
			self.outdir = Path(outdir)
		
		lang_list = ['en', 'ja']
		self.ocr_engine = EasyOCREngine(lang_list)
		self.reader = ReceiptReader(self.ocr_engine)
		self.preprocess_types = [
			('crop', { 'size_scale': (1.0, 1.0) }),
			# ('closing', { }),
			('greyscale', { }),
			# ('gamma_correction', { 'gamma': 0.9 }),
			('unsharp_masking', { 'alpha': 1.6 }),
		]
	
	def read(self, path):
		try:
			result: ReadResult = self.reader.recognize(path, self.preprocess_types)
			
			overlay: np.ndarray = result.render_text_overlay()
			
			path = Path(path)
			
			self.outdir.mkdir(exist_ok=True)
			cv2.imwrite(str(self.outdir / f'{path.stem}_debug1.png'), result.ocr_result.image)
			cv2.imwrite(str(self.outdir / f'{path.stem}_debug2.png'), overlay)
			
			for line in result.lines:
				print(r"-----")
				for box in line:
					bbox = box.bbox
					print(f"{format_bbox(bbox)}: {box.height} # {box.text}")
			
			print(f"Receipt Data:")
			print(result.receipt_data)
		except Exception as e:
			traceback.print_exc()

def main():
	tester = Tester()
	
	while True:
		print("Input image filepath:")
		raw = input().strip(' ').strip('"')
		
		if raw:
			tester.read(raw)

if __name__ == '__main__':
	main()
