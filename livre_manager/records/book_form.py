"""
records/book_form.py
"""

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from .form_util import ImageWidget
from .models import Book, BookAuthorRelation, validate_datetime

class BookForm(forms.ModelForm):
	class Meta:
		FieldMap = {
			'title': { 'label': 'タイトル', 'widget': forms.TextInput() },
			'series': { 'label': 'シリーズ・レーベル', 'widget': forms.TextInput() },
			'isbn': { 'label': 'ISBN', 'widget': forms.TextInput() },
			'jan': { 'label': 'JAN', 'widget': forms.TextInput() },
			'asin': { 'label': 'ASIN', 'widget': forms.TextInput() },
			'publisher': { 'label': '出版社', 'widget': forms.TextInput() },
			'publication_date_str': { 'label': '出版日', 'widget': forms.TextInput(attrs={ 'placeholder': '例: 2020/4/10' }) },
			'price': { 'label': '定価' },
			'currency_code': { 'label': '通貨' },
			'cover_image': { 'label': 'カバー画像' },
			'user_memo': { 'label': 'メモ', 'widget': forms.Textarea() },
		}
		
		model = Book
		fields = list(FieldMap.keys())
		labels = { name: v['label'] for name, v in FieldMap.items() if 'label' in v }
		widgets = { name: v['widget'] for name, v in FieldMap.items() if 'widget' in v }

AUTHOR_FIELD_MAP = {
	'author_name': { 'label': '著者名', 'widget': forms.TextInput() },
	'role': { 'label': '役割', 'widget': forms.TextInput() },
}

class AuthorForm(forms.ModelForm):
	class Meta:
		model = BookAuthorRelation
		fields = list(AUTHOR_FIELD_MAP.keys())
		labels = { name: v['label'] for name, v in AUTHOR_FIELD_MAP.items() if 'label' in v }
		widgets = { name: v['widget'] for name, v in AUTHOR_FIELD_MAP.items() if 'widget' in v }

AuthorFormSet = inlineformset_factory(
	parent_model=Book,
	model=BookAuthorRelation,
	form=AuthorForm,
	extra=5,  # 最初から表示される行数
	can_delete=True,  # 行の削除を許可するか
	can_order=True,
)
