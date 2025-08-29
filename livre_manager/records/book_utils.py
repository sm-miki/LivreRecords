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
