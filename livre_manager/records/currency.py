"""
records/currency.py
"""
NULL_CURRENCY_CODE = ''
JPY = 'JPY'
USD = 'USD'

CURRENCY_INFO = {
	'JPY': { 'symbol': '¥', 'label': '円', 'base_decimal_place': 0 },
	'USD': { 'symbol': '$', 'label': '米ドル', 'base_decimal_place': 2 },
	'EUR': { 'symbol': '€', 'label': 'ユーロ', 'base_decimal_place': 2 },
	'GBP': { 'symbol': '£', 'label': 'ポンド', 'base_decimal_place': 2 },
}

CURRENCY_CODE_CHOICES = {
	NULL_CURRENCY_CODE: u"---",
	**{ code: info['label'] for code, info in CURRENCY_INFO.items() },
}
CURRENCY_SYMBOLS = {
	code: info['symbol'] for code, info in CURRENCY_INFO.items()
}
