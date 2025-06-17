from django import template
from decimal import Decimal

register = template.Library()

# @register.filter
# def attr(obj, name):
# 	return getattr(obj, name)


def format_decimal(value):
	s = f"{value:,.6f}"
	
	# 末尾の不要な0を削除する
	point = s.find('.')
	if point != -1:
		for i in range(len(s) - 1, point - 1, -1):
			match s[i]:
				case '0':
					pass
				case '.':
					s = s[:i] if i != 0 else '0'
					break
				case _:
					s = s[:i + 1]
					break
	return s

CURRENCY_SYMBOLS = {
	'JPY': '￥',
	'USD': '＄',
	'EUR': '€',
}

@register.filter
def currency_format(amount, currency_code):
	symbol = CURRENCY_SYMBOLS.get(currency_code, '')
	return f"{symbol}{format_decimal(amount)}"
