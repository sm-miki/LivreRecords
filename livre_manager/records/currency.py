NULL_CURRENCY_CODE = ''
JPY = 'JPY'
USD = 'USD'

CURRENCY_INFO = {
	'JPY': { 'symbol': '¥', 'label': '円' },
	'USD': { 'symbol': '$', 'label': 'ドル(USD)' },
	'EUR': { 'symbol': '€', 'label': 'ユーロ' },
	'GBP': { 'symbol': '£', 'label': 'ポンド' },
}

CURRENCY_CODE_CHOICES = {
	NULL_CURRENCY_CODE: u"---",
	**{ code: info['label'] for code, info in CURRENCY_INFO.items() },
}
CURRENCY_SYMBOLS = {
	code: info['symbol'] for code, info in CURRENCY_INFO.items()
}