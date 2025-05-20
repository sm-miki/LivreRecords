import math
from collections import deque
import cv2
import numpy as np

def crop_receipt(image, size_scale=1):
	"""
	入力画像からレシート領域を抽出する。
	入力画像は以下のような条件を満たすことが好ましい。
	 - 背景が無地である、または輪郭が少ない
	 - 背景がレシートよりも暗い色である
	 - レシートが中央に配置されている
	"""
	imdim = np.min(image.shape[:2])
	orig = image.copy()
	
	""" 1. ノイズ除去 """
	ksize = 5
	image = cv2.GaussianBlur(image, (ksize, ksize), 0)
	
	""" 2. ノイズ除去・領域強調: クロージング処理で穴埋め、膨張・収縮で連続領域を強調 """
	ksize = max(1, int(imdim * 0.002)) * 2 + 1
	kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
	image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=3)
	
	""" 3. 白色強調 """
	whiteness_gamma = 1.8  # マスクのガンマ値
	h, s, v = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32))
	p = (1 - s / 255)  # 白っぽさ（彩度が低い画素を高輝度とみなす）
	p_min, p_max = np.min(p), np.max(p)
	if p_max > p_min:
		# "白っぽさ" でマスキングする
		p = (p - p_min) / (p_max - p_min)  # 輝度マスク
		grey = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_BGR2GRAY)
		image = grey * np.float_power(p, whiteness_gamma)
		
		# 画像の正規化
		neg_median_ratio = 0.05
		median = np.median(image, axis=(0, 1))  # 画像全体が白い場合に平均画素値を低減させるための補正項
		mean = np.clip(
			np.mean(np.mean(image, axis=(0, 1)) - neg_median_ratio * median),
			0, 255
		)
		std = np.mean(np.std(image, axis=(0, 1)))
		image = np.clip((image - mean) * 255.0 / std + 127.5, 0, 255)
	
	""" 4. 白色領域の抽出 (二値化) """
	lower, upper = 175, 255
	image = cv2.inRange(image, lower, upper)  # 閾値による二値化
	
	# 二値化画像 binary （0 or 255）を前提
	numLabels, labels, stats, centroids = cv2.connectedComponentsWithStats(image, connectivity=8)
	if len(stats) > 1:
		# 背景ラベル 0 を除き、最大面積のラベルを取得
		areas = stats[1:, cv2.CC_STAT_AREA]
		max_label = 1 + np.argmax(areas)
		
		# 最大白色領域だけを抜き出す
		image = image * (labels == max_label)
	
	""" 5. 線分検出による輪郭決定 """
	pts = _hough_bounding(image)
	if pts is None:
		return orig
	
	""" 6. 透視変換 """
	if isinstance(size_scale, (int, float)):
		size_scale = (size_scale, size_scale)
	
	rect = _order_points(pts)
	(tl, tr, br, bl) = rect
	min_width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)) * size_scale[0])
	min_height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)) * size_scale[1])
	dst = np.array([[0, 0],
							[min_width - 1, 0],
							[min_width - 1, min_height - 1],
							[0, min_height - 1]], dtype="float32")
	M = cv2.getPerspectiveTransform(rect, dst)
	warped = cv2.warpPerspective(orig, M, (min_width, min_height))
	
	return warped

def _order_points(pts):
	"""4点の座標を左上、右上、右下、左下の順に並べ替える"""
	rect = np.zeros((4, 2), dtype="float32")
	s = pts.sum(axis=1)
	rect[0] = pts[np.argmin(s)]  # 左上：x+y最小
	rect[2] = pts[np.argmax(s)]  # 右下：x+y最大
	
	diff = np.diff(pts, axis=1)
	rect[1] = pts[np.argmin(diff)]  # 右上：x-yが最小
	rect[3] = pts[np.argmax(diff)]  # 左下：x-yが最大
	return rect

def _hough_bounding(image):
	h, w = image.shape[:2]
	imdim = min(h, w)
	
	# (1) エッジ検出
	edges = cv2.Canny(image, 50, 190, apertureSize=3)
	
	# (2) ハフ変換で輪郭を線分として検出する
	minLineLength = imdim * 0.02
	maxLineGap = imdim * 0.075
	lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 95, minLineLength=minLineLength, maxLineGap=maxLineGap)
	if lines is None:
		return None  # 検出失敗時
	
	lines = lines.reshape(-1, 4)
	
	# (3) 線分を水平・垂直に分類
	horizontals, verticals = deque(), deque()
	for x1, y1, x2, y2 in lines:
		angle = np.degrees(np.arctan2((y2 - y1), (x2 - x1)))
		if abs(angle) < 45:
			horizontals.append((x1, y1, x2, y2))
		else:
			verticals.append((x1, y1, x2, y2))
	
	# (4) 最外縁線分の近くにある線分のみを選んで境界線を平滑化する
	th = int(imdim * 0.12)  # 外縁エッジの近傍半径
	
	top_line = (0, 0, w - 1, 0)
	bottom_line = (0, h - 1, w - 1, h - 1)
	if horizontals:
		# 水平線分を上下に分類
		horizontals = np.array(horizontals)
		is_latter = (horizontals[:, 1] + horizontals[:, 3]) > h
		top_segs = horizontals[~is_latter]
		bottom_segs = horizontals[is_latter]
		
		# 上端輪郭（水平線）の決定
		if len(top_segs) != 0:
			# 最も上に位置する線分 (最外縁線分)
			outer_seg = top_segs[np.argmin(top_segs[:, 1] + top_segs[:, 3])]
			# 最外縁線分の近傍線分を抽出
			neighbor_segs = np.array(
				[seg for seg in top_segs if _is_segment_on_extension(seg, outer_seg, thresh=th)]
			)
			top_line = _get_smooth_line(neighbor_segs, image.shape)
		
		# 下端輪郭（水平線）の決定
		if len(bottom_segs) != 0:
			# 最も上に位置する線分 (最外縁線分)
			outer_seg = bottom_segs[np.argmax(bottom_segs[:, 1] + bottom_segs[:, 3])]
			# 最外縁線分の近傍線分を抽出
			neighbor_segs = np.array(
				[seg for seg in bottom_segs if _is_segment_on_extension(seg, outer_seg, thresh=th)]
			)
			bottom_line = _get_smooth_line(neighbor_segs, image.shape)
	
	left_line = (0, 0, 0, h - 1)
	right_line = (w - 1, 0, w - 1, h - 1)
	if verticals:
		# 垂直線分を左右に分類
		verticals = np.array(verticals)
		is_latter = (verticals[:, 0] + verticals[:, 2]) > w
		left_segs = verticals[~is_latter]
		right_segs = verticals[is_latter]
		
		# 左端輪郭（水平線）の決定
		if len(left_segs) != 0:
			# 最も上に位置する線分 (最外縁線分)
			outer_seg = left_segs[np.argmin(left_segs[:, 0] + left_segs[:, 2])]
			# 最外縁線分の近傍線分を抽出
			neighbor_segs = np.array(
				[seg for seg in left_segs if _is_segment_on_extension(seg, outer_seg, thresh=th)]
			)
			left_line = _get_smooth_line(neighbor_segs, image.shape)
		
		# 右端輪郭（水平線）の決定
		if len(right_segs) != 0:
			# 最も上に位置する線分 (最外縁線分)
			outer_seg = right_segs[np.argmax(right_segs[:, 0] + right_segs[:, 2])]
			# 最外縁線分の近傍線分を抽出
			neighbor_segs = np.array(
				[seg for seg in right_segs if _is_segment_on_extension(seg, outer_seg, thresh=th)]
			)
			right_line = _get_smooth_line(neighbor_segs, image.shape)
	
	# (5) 交点4つを計算
	pts = [
		_line_intersection(top_line, left_line),
		_line_intersection(top_line, right_line),
		_line_intersection(bottom_line, right_line),
		_line_intersection(bottom_line, left_line),
	]
	pts = np.array(pts, dtype="float32")
	
	return pts

def _is_segment_on_extension(seg, base_seg, thresh=20):
	"""base_segの延長線上にsegが乗っているかを捉える (両端点が閾値以内にある場合)"""
	x1, y1, x2, y2 = base_seg
	dx, dy = x2 - x1, y2 - y1
	norm = math.hypot(dx, dy)
	if norm == 0:
		return False
	#ax + by + c = 0
	a, b = dy, -dx
	c = dx * y1 - dy * x1
	# 両端点の距離をチェック
	for x, y in [(seg[0], seg[1]), (seg[2], seg[3])]:
		dist = abs(a * x + b * y + c) / norm
		if dist > thresh:
			return False
	return True

def _get_smooth_line(
		segments: np.ndarray, image_shape, vertical=False
) -> tuple[int, ...]:
	"""
	線分集合をもとにRANSACではなくcv2.fitLineでロバストに直線を推定し、
	画像端との交点を返す

	Args:
		segments: [n, 4] の大きさの配列。各要素は (x1, y1, x2, y2) のように直線を表す座標。
		image_shape:
		vertical:

	Returns:

	"""
	# 全セグメントの両端点を集約
	pts = segments[:, :2].reshape(-1, 2)
	pts = np.vstack((pts, segments[:, 2:]))
	
	# fitLineで直線を推定
	vx, vy, x0, y0 = cv2.fitLine(pts.astype(np.float32), cv2.DIST_L2, 0, 0.01, 0.01).flatten()
	h, w = image_shape[:2]
	if not vertical:
		if abs(vy) < 1e-6:
			# ほぼ水平な直線の場合
			return 0, int(round(y0)), w - 1, int(round(y0))
		else:
			# y=0 および y=h との交点を計算
			t_top = (0 - y0) / vy
			t_bot = (h - 1 - y0) / vy
			p1_x = int(round(x0 + t_top * vx))
			p2_x = int(round(x0 + t_bot * vx))
			return p1_x, 0, p2_x, h - 1
	else:
		if abs(vx) < 1e-6:
			# ほぼ垂直な直線の場合
			return int(round(x0)), 0, int(round(x0)), h - 1
		else:
			# x=0 および x=w との交点を計算
			t_left = (0 - x0) / vx
			t_right = (w - 1 - x0) / vx
			
			p1_y = int(round(y0 + t_left * vy))
			p2_y = int(round(y0 + t_right * vy))
			return 0, p1_y, w - 1, p2_y

def _line_intersection(line1, line2):
	# 交点計算
	# line: (x1,y1,x2,y2)
	x1, y1, x2, y2 = line1
	x3, y3, x4, y4 = line2
	
	denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
	if denom == 0:
		return None
	ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
	return x1 + ua * (x2 - x1), y1 + ua * (y2 - y1)

def closing(image, ksize=(3, 3), iterations=1):
	kernel_erode = np.ones(ksize, np.uint8)
	image = cv2.erode(image, kernel_erode, iterations=iterations)
	
	# 膨張処理（気持ち大きめに）
	kernel_dilate = np.ones(ksize, np.uint8)
	image = cv2.dilate(image, kernel_dilate, iterations=iterations)
	
	return image

def gamma_correction(image, gamma):
	converted_value = 255 * np.float_power((image / 255), 1 / gamma)
	
	return converted_value

def greyscale(image):
	return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def unsharp_masking(image, blur_ksize=(5, 5), alpha=1.5):
	"""
	
	Args:
		image:
		blur_ksize:
		alpha: 強度

	Returns:

	"""
	
	# ガウシアンぼかしを適用
	blurred = cv2.GaussianBlur(image, blur_ksize, 0)
	
	# アンシャープマスクの適用
	sharpened = np.clip((1 + alpha) * image - alpha * blurred, 0, 255)
	
	return sharpened
