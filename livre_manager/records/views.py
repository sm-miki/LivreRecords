from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.views.generic import TemplateView

from .obtain_form import ObtainForm, ObtainedItemForm, ObtainItemFormSet

# トップページ
def index(request):
	return render(request, 'records/index.html')

# 入手記録一覧画面
def obtains(request):
	return render(request, 'records/obtains.html')

# # 入手記録入力画面
# def obtain_edit(request):
# 	my_dict = {
# 		'insert_something': "views.pyのinsert_something部分です。",
# 		'name': 'Bashi',
# 		# 'test_titles': ['title 1', 'title 2', 'title 3'],
# 		'form': ObtainForm(),  # 追加
# 	}
# 	return render(request, 'records/obtain_edit.html', my_dict)

class ObtainEditView(TemplateView):
	def __init__(self):
		self.params = {
			'PostSuccess': False,
			'obtain_form': ObtainForm(),
			'item_formset': ObtainItemFormSet(),
			'item_columns': ObtainedItemForm.Meta.labels.values(),
			
		}
	
	def get(self, request, *args, **kwargs):
		
		self.params['obtain_form'] = ObtainForm()
		self.params['item_formset'] = ObtainItemFormSet()
		self.params['PostSuccess'] = False
		return render(request, 'records/obtain_edit.html', context=self.params)
	
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
			self.params['PostSuccess'] = True
		else:
			# フォームが有効ではない場合、
			# errorsにエラー内容が格納される。
			print(obtain_form.errors)
			
			obtain_form = ObtainForm()
			item_formset = ObtainItemFormSet()
		
		self.params.update({
			'obtain_form': obtain_form,
			'item_formset': item_formset,
		})
		
		return render(request, 'records/obtain_edit.html', context=self.params)

# 入手記録詳細画面
def obtain_detail(request, pk):
	context = { "obtain_id": pk }
	return render(request, 'records/obtain_detail.html', context)

# 書籍一覧画面
def items(request):
	return render(request, 'records/items.html')

# 書籍情報編集画面
def item_edit(request):
	return render(request, 'records/item_edit.html')

# 書籍詳細画面
def item_detail(request, pk):
	context = { "item_id": pk }
	return render(request, 'records/item_detail.html', context)

# 統計画面
def stats(request):
	return render(request, 'records/stats.html')
