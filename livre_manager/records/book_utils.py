from typing import Dict

def isbn10_to_isbn13(isbn10: str) -> str:
	"""
	ISBN10をISBN13に変換する。
	"""
	isbn10 = isbn10.replace('-', '').upper()
	if len(isbn10) != 10 or not isbn10[:-1].isdigit() or (isbn10[-1] not in '0123456789X'):
		raise ValueError("Invalid ISBN-10 format")
	
	prefix = '978'
	core = isbn10[:-1]
	
	isbn13_base = prefix + core
	sum_ = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(isbn13_base))
	check_digit_value = (10 - (sum_ % 10)) % 10
	
	return isbn13_base + str(check_digit_value)

def isbn13_to_isbn10(isbn13: str) -> str:
	"""
	ISBN13をISBN10に変換する。978から始まらないISBN13の場合はNoneを返す。
	"""
	# Remove any hyphens
	isbn13 = isbn13.replace('-', '')
	if len(isbn13) != 13 or not isbn13.isdigit():
		raise ValueError("Invalid ISBN-13 format")
	
	if not isbn13.startswith('978'):
		return None
	
	core = isbn13[3:-1]
	
	# Calculate ISBN-10 check digit
	s = sum(int(digit) * (i + 1) for i, digit in enumerate(core))
	check_digit_value = s % 11
	check_digit = 'X' if check_digit_value == 10 else str(check_digit_value)
	
	return core + check_digit

def get_external_links(isbn) -> Dict[str, Dict]:
	if isbn is None or len(isbn) not in (10, 13):
		return { }
	
	links = { }
	
	try:
		if len(isbn) == 10:
			isbn13 = isbn10_to_isbn13(isbn)
			isbn10 = isbn
		else:
			isbn13 = isbn
			isbn10 = isbn13_to_isbn10(isbn)
	except ValueError:
		return { }
	
	# ジュンク堂
	if isbn13:
		links['junkudo'] = {
			'label': 'ジュンク堂', 'url': f"https://www.maruzenjunkudo.co.jp/products/{isbn13}"
		}
		links['kinokuniya'] = {
			'label': '紀伊國屋', 'url': f"https://www.kinokuniya.co.jp/f/dsg-01-{isbn13}"
		}
	
	if isbn10:
		links['amazon'] = {
			'label': 'Amazon', 'url': f"https://www.amazon.co.jp/dp/{isbn10}"
		}
	
	return links
