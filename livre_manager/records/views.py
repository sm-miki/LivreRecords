from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.views.generic import TemplateView

from .models import ObtainRecord
from .obtain_form import ObtainForm, ObtainedItemForm, ObtainItemFormSet

# トップページ
def index(request):
	return render(request, 'records/index.html')

# 入手記録一覧画面
def obtain_list(request):
	# 動的にモデルのフィールドを取得
	model = ObtainRecord
	fields = [f for f in model._meta.fields if f.name not in model.READONLY_FIELDS]
	
	# フィールド名とヘッダー用ラベルを準備
	headers = [f.verbose_name for f in fields]
	field_names = [f.name for f in fields]
	
	# 全レコードを取得
	records = model.objects.all()
	
	context = {
		'headers': headers,
		'field_names': field_names,
		'records': records,
	}
	return render(request, 'records/obtain_list.html', context)
	
	# return render(request, 'records/obtains.html')

class ObtainEditView(TemplateView):
	def __init__(self):
		self.context = {
			'PostSuccess': False,
			'obtain_form': ObtainForm(),
			'item_formset': ObtainItemFormSet(),
			'item_columns': ObtainedItemForm.Meta.labels.values(),
		}
	
	def get(self, request, *args, **kwargs):
		self.context['obtain_form'] = ObtainForm()
		self.context['item_formset'] = ObtainItemFormSet()
		self.context['PostSuccess'] = False
		return render(request, 'records/obtain_edit.html', context=self.context)
	
	def post(self, request):
		"""
		POSTリクエストの処理
		
		Args:
			request:

		Returns:

		"""
		obtain_form = ObtainForm(request.POST, request.FILES)
		item_formset = ObtainItemFormSet(request.POST, request.FILES)
		
		if obtain_form.is_valid() and item_formset.is_valid():
			with transaction.atomic():  # データベース操作をアトミックに実行
				obtain = obtain_form.save()
				item_formset.instance = obtain  # Formsetに親インスタンスを紐付け
				item_formset.save()
			# return redirect('receipt_success')  # 成功ページへリダイレクト
			
			self.context.update({
				'obtain_form': ObtainForm(),
				'item_formset': ObtainItemFormSet(),
			})
			
			self.context['PostSuccess'] = True
		else:
			# フォームが有効ではない場合、
			# errorsにエラー内容が格納される。
			print(obtain_form.errors)
			print(item_formset.errors)
		
		return render(request, 'records/obtain_edit.html', context=self.context)

# 入手記録詳細画面
def obtain_detail(request, pk):
	context = {
		'obtain_id': pk,
	}
	return render(request, 'records/obtain_detail.html', context=context)

# 書籍一覧画面
def items(request):
	context = {
	}
	return render(request, 'records/items.html', context=context)

# 書籍情報編集画面
def item_edit(request):
	context = {
	}
	return render(request, 'records/item_edit.html', context=context)

# 書籍詳細画面
def item_detail(request, pk):
	context = {
		"item_id": pk,
	}
	return render(request, 'records/item_detail.html', context=context)

# 統計画面
def stats(request):
	context = {
	}
	return render(request, 'records/stats.html', context=context)
