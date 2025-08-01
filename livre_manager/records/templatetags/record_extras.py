from decimal import Decimal
import six
from django import template
from django.template.base import Node
from django.urls import reverse, reverse_lazy
from django.utils.functional import keep_lazy

from ..models import Book
from ..currency import CURRENCY_SYMBOLS

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

@register.filter
def format_currency(amount, currency_code):
	if amount is None:
		return None
	
	symbol = CURRENCY_SYMBOLS.get(currency_code, '')
	return f"{symbol}{format_decimal(amount)}"

@register.simple_tag
def format_price_and_tax(price, net_price, tax, currency_code) -> str:
	s = ""
	if net_price is not None:
		if tax is not None:
			s = f"税抜 {format_currency(net_price, currency_code)} + 税 {format_currency(tax, currency_code)}"
		else:
			s = f"税 {format_currency(tax, currency_code)}"
	elif tax is not None:
		s = f"税 {format_currency(tax, currency_code)}"
	
	if price is None:
		return s
	elif s:
		return f"税込 {format_currency(price, currency_code)} ({s})"
	else:
		return f"税込 {format_currency(price, currency_code)}"

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

# Djangoテンプレートタグと文字列の間の改行を削除する
# 参考: https://stackoverflow.com/questions/33479363/remove-line-breaks-from-django-template/33479624
@register.tag
def linebreakless(parser, token):
	nodelist = parser.parse(('endlinebreakless',))
	parser.delete_first_token()
	return LinebreaklessNode(nodelist)

class LinebreaklessNode(Node):
	def __init__(self, nodelist):
		self.nodelist = nodelist
	
	def render(self, context):
		strip_line_breaks = keep_lazy(six.text_type)(lambda x: x.replace('\n\n', '\n'))
		
		return strip_line_breaks(self.nodelist.render(context).strip())
