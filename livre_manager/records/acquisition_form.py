"""
acquisition_form.py
"""
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from .form_util import ImageWidget
from .models import Acquisition, AcquiredItem, validate_datetime

class AcquisitionForm(forms.ModelForm):
	class Meta:
		FieldMap = {
			'acquisition_type': { 'label': '入手方法', 'widget': forms.RadioSelect(attrs={ 'class': 'inline-radio' }) },
			'acquisition_date_str': { 'label': '入手日時', 'widget': forms.TextInput(attrs={ 'placeholder': '例: 2020/4/10 15:20:33' }) },
			'acquisition_date_tz': { 'label': 'タイムゾーン' },
			'store_name': { 'label': '店舗名', 'widget': forms.TextInput() },
			'transaction_number': { 'label': '取引番号', 'widget': forms.TextInput() },
			'transaction_context': { 'label': 'その他取引情報', 'widget': forms.TextInput() },
			'staff': { 'label': '担当者', 'widget': forms.TextInput() },
			'currency_code': { 'label': '通貨単位' },
			'total': { 'label': '支払金額' },
			'subtotal': { 'label': '小計（税抜）' },
			'tax': { 'label': '税額' },
			'extra_fee': { 'label': '送料等' },
			'payment_method': { 'label': '支払方法' },
			'receipt_image': { 'label': 'レシート画像' },
		}
		
		model = Acquisition
		fields = list(FieldMap.keys())
		labels = { name: v['label'] for name, v in FieldMap.items() if 'label' in v }
		widgets = { name: v['widget'] for name, v in FieldMap.items() if 'widget' in v }
	
ACQUIRED_ITEM_FIELD_MAP = {
	'item_type': { 'label': '種類' },
	'item_id': { 'label': '商品・書籍ID(ISBN)', 'widget': forms.TextInput() },
	'genre_code': { 'label': '分類', 'widget': forms.TextInput() },
	'description': { 'label': '商品説明', 'widget': forms.TextInput() },
	'price': { 'label': '税込価格' },
	'net_price': { 'label': '税抜価格' },
	'tax': { 'label': '税額' },
	'quantity': { 'label': '数量' },
	'user_memo': { 'label': 'メモ', 'widget': forms.TextInput() },
}

class AcquiredItemForm(forms.ModelForm):
	class Meta:
		model = AcquiredItem
		fields = list(ACQUIRED_ITEM_FIELD_MAP.keys())
		labels = { name: v['label'] for name, v in ACQUIRED_ITEM_FIELD_MAP.items() if 'label' in v }
		widgets = { name: v['widget'] for name, v in ACQUIRED_ITEM_FIELD_MAP.items() if 'widget' in v }

AcquisitionItemFormSet = inlineformset_factory(
	parent_model=Acquisition,
	model=AcquiredItem,
	form=AcquiredItemForm,
	extra=10,  # 最初から表示される行数
	can_delete=True,  # 行の削除を許可するか
	can_order=True,
)
