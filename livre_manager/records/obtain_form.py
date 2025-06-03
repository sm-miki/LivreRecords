from django import forms
from django.forms import inlineformset_factory

from .form_util import ImageWidget
from .models import ObtainRecord, ObtainedItem

class ObtainForm(forms.ModelForm):
	class Meta:
		FieldMap = {
			'obtain_type': { 'label': '入手方法', 'widget': forms.RadioSelect(attrs={ 'class': 'inline-radio' }) },
			'store_name': { 'label': '店舗名', 'widget': forms.TextInput() },
			'obtain_date_str': { 'label': '入手日時', 'widget': forms.TextInput() },
			'transaction_number': { 'label': '取引番号', 'widget': forms.TextInput() },
			'transaction_context': { 'label': 'その他取引情報', 'widget': forms.TextInput() },
			'staff': { 'label': '担当者情報', 'widget': forms.TextInput() },
			'currency_unit': { 'label': '通貨単位' },
			'total': { 'label': '支払金額' },
			'subtotal': { 'label': '税抜合計' },
			'tax': { 'label': '税額' },
			'payment_method': { 'label': '支払方法' },
			'receipt_image': { 'label': 'レシート画像' },
		}
		
		model = ObtainRecord
		fields = list(FieldMap.keys())
		labels = { name: v['label'] for name, v in FieldMap.items() if 'label' in v }
		widgets = { name: v['widget'] for name, v in FieldMap.items() if 'widget' in v }

OBTAINED_ITEM_FIELD_MAP = {
	'item_type': { 'label': '種類' },
	'item_id': { 'label': '商品・書籍ID(ISBN)', 'widget': forms.TextInput() },
	'genre_code': { 'label': 'ジャンルコード' ,'widget': forms.TextInput() },
	'description': { 'label': '商品名・説明', 'widget': forms.TextInput() },
	'net_price': { 'label': '税抜価格' },
	'price': { 'label': '税込価格' },
	'tax': { 'label': '税額' },
	'quantity': { 'label': '数量' },
	'user_memo': { 'label': 'メモ' , 'widget': forms.TextInput() },
}

class ObtainedItemForm(forms.ModelForm):
	class Meta:
		model = ObtainedItem
		fields = list(OBTAINED_ITEM_FIELD_MAP.keys())
		labels = { name: v['label'] for name, v in OBTAINED_ITEM_FIELD_MAP.items() if 'label' in v }
		widgets = { name: v['widget'] for name, v in OBTAINED_ITEM_FIELD_MAP.items() if 'widget' in v }
		
ObtainItemFormSet = inlineformset_factory(
	parent_model=ObtainRecord,
	model=ObtainedItem,
	form=ObtainedItemForm,
	extra=10,  # 最初から表示される行数
	can_delete=True,  # 行の削除を許可するか
)
