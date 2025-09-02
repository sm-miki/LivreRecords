"""
records/book_form.py
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
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
	'order': { 'widget': forms.HiddenInput() },
	'author_name': { 'label': '著者名', 'widget': forms.TextInput() },
	'role': { 'label': '役割', 'widget': forms.TextInput() },
}

class AuthorForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# フォームレベルでは未入力を許容する。（入力されていないレコードは削除される。）
		self.fields['author_name'].required = False
	
	class Meta:
		model = BookAuthorRelation
		fields = list(AUTHOR_FIELD_MAP.keys())
		labels = { name: v['label'] for name, v in AUTHOR_FIELD_MAP.items() if 'label' in v }
		widgets = { name: v['widget'] for name, v in AUTHOR_FIELD_MAP.items() if 'widget' in v }

class BaseAuthorFormSet(BaseInlineFormSet):
	"""
	著者用のカスタムFormSet。
	- DELETEフィールドを非表示にします。
	- 動的に追加・削除されたフォームのバリデーションを処理します。
	"""
	
	def add_fields(self, form, index):
		super().add_fields(form, index)
		# 削除フィールドをチェックボックスから隠しフィールドに変更
		form.fields[forms.formsets.DELETION_FIELD_NAME].widget = forms.HiddenInput()
	
	def clean(self):
		"""
		フォームセットのバリデーション。
		未入力の新規フォームを無視し、入力途中のフォームを検証する。
		"""
		super().clean()
		
		if any(self.errors):
			return
		
		for form in self.forms:
			if not form.has_changed():
				continue
			
			is_empty = not form.cleaned_data.get('author_name') and not form.cleaned_data.get('role')
			
			if self.can_delete and is_empty and not form.instance.pk:
				form.cleaned_data[forms.formsets.DELETION_FIELD_NAME] = True
			elif not is_empty and not form.cleaned_data.get('author_name'):
				form.add_error('author_name', 'このフィールドは必須です。')

AuthorFormSet = inlineformset_factory(
	parent_model=Book,
	model=BookAuthorRelation,
	form=AuthorForm,
	formset=BaseAuthorFormSet,
	extra=0,
	can_delete=True,  # 行の削除を許可するか
)
