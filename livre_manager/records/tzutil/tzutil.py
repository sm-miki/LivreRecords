from datetime import datetime, timedelta
import pytz

_CONTINENT_LIST = {
	"Africa",
	"America",
	"Antarctica",
	"Arctic",
	"Asia",
	"Atlantic",
	"Australia",
	"Europe",
	"Indian",
	"Pacific",
}

def _is_available_timezone(name):
	# 出力するべきタイムゾーン名かどうかを判定する。
	# 大陸名/都市名 の形式のみを採用する。
	return (
			"/" in name and
			name.split("/")[0] in _CONTINENT_LIST
	)

def format_utcoffset(utcoffset) -> str:
	"""Format a timedelta as "+HH:MM" or "-HH:MM"."""
	sign = "+" if utcoffset >= 0 else "-"
	hours, minutes = divmod(abs(int(utcoffset)) // 60, 60)
	return f"{sign}{hours:02d}:{minutes:02d}"

def _init():
	utc = pytz.utc
	# Pick two dates to check standard and DST offsets.
	dt_picked = [
		datetime(2020, 2, 15, 12, 0, tzinfo=utc),
		datetime(2020, 5, 15, 12, 0, tzinfo=utc),
		datetime(2020, 8, 15, 12, 0, tzinfo=utc),
		datetime(2020, 11, 15, 12, 0, tzinfo=utc),
	]
	
	entries = []  # tuples of (name, standard_offset_timedelta, dst_offset_timedelta)
	
	for name in filter(_is_available_timezone, pytz.all_timezones):
		tz = pytz.timezone(name)
		# Convert the same UTC instant to the timezone to get the local offset.
		off = [
			dt.astimezone(tz).utcoffset() or timedelta(0) for dt in dt_picked
		]
		# Standard offset is the smaller of the two offsets (DST usually increases offset).
		std = min(off)
		dst = max(off)
		entries.append((name, std.total_seconds(), dst.total_seconds()))
	
	# Sort by standard offset (seconds), then by timezone name
	entries.sort(key=lambda t: (t[1], t[0]))
	
	# UTCを追加
	entries.insert(0, ("UTC", 0, 0))
	
	for name, std, dst in entries:
		ALL_TIMEZONE_NAMES.append(name)
		ALL_TIMEZONE_DATA[name] = {
			"name": name,
			"name_with_offset": _tz_name_with_offset(name, std, dst)
		}

def _tz_name_with_offset(name, std, dst):
	"""
	タイムゾーンの名称をUTCオフセットと共に取得する。
	
	Args:
		name (str): タイムゾーン名。

	Returns:
		str: タイムゾーンの名称とUTCオフセットを含む文字列。例: (UTC+09:00) Asia/Tokyo, (UTC+05:00/+04:00) America/New_York
	"""
	# 標準時
	std_str = format_utcoffset(std)
	
	# 夏時間（設定されている場合のみ）
	if dst is None or std == dst:
		return f"{name} [UTC{std_str}]"
	else:
		dst_str = format_utcoffset(dst)
		return f"{name} [UTC{std_str}/{dst_str}]"

def get_tzinfo(name):
	return pytz.timezone(name)

ALL_TIMEZONE_NAMES = []
ALL_TIMEZONE_DATA = { }
_init()
