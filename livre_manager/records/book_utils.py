def isbn10_to_isbn13(isbn10: str) -> str:
	"""
	ISBN10をISBN13に変換する。
	"""
	if len(isbn10) != 10 or not isbn10[:-1].isdigit() or (isbn10[-1] not in '0123456789X'):
		raise ValueError("Invalid ISBN-10 format")
	
	isbn10 = isbn10.replace('-', '')
	
	prefix = '978'
	core = isbn10[:-1]
	
	isbn13 = prefix + core
	sum_ = sum(int(isbn13[i]) * (1 if i % 2 == 0 else 3) for i in range(len(isbn13)))
	check_digit_value = (10 - (sum_ % 10)) % 10
	
	return isbn13 + str(check_digit_value)

def isbn13_to_isbn10(isbn13: str) -> str:
	"""
	ISBN13をISBN10に変換する。
	"""
	if len(isbn13) != 13 or not isbn13.isdigit():
		raise ValueError("Invalid ISBN-13 format")
	
	# Remove any hyphens
	isbn13 = isbn13.replace('-', '')
	
	if not isbn13.startswith('978'):
		raise ValueError("ISBN-13 must start with '978' for conversion to ISBN-10")
	
	core = isbn13[3:-1]
	check_digit_value = sum(int(isbn13[i]) * (1 if i % 2 == 0 else 3) for i in range(len(isbn13))) % 10
	check_digit = 'X' if check_digit_value == 10 else str(check_digit_value)
	
	return core + check_digit
