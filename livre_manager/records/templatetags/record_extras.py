from decimal import Decimal
from django import template
from django.urls import reverse, reverse_lazy

from ..models import Book

register = template.Library()

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
	if amount is None:
		return None
	
	symbol = CURRENCY_SYMBOLS.get(currency_code, '')
	return f"{symbol}{format_decimal(amount)}"

# @register.simple_tag
# def book_detail_url(isbn):
# 	"""
# 	与えられた ISBN（item_id）に該当する Book があれば、その詳細ページの URL を返す。
# 	なければ空文字を返す。
# 	"""
# 	try:
# 		book = Book.objects.get(isbn=isbn)
# 		return reverse('records:book_detail', args=[book.pk])
# 	except Book.DoesNotExist:
# 		return ''
