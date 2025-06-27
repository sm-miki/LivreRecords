"""
records/views.py
"""
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.utils import timezone
from django.contrib import messages
from django.views.generic import TemplateView

from .models import AcquisitionRecord, Book, BookAuthorRelation
from .acquisition_form import AcquisitionForm, AcquiredItemForm, AcquisitionItemFormSet
from .book_form import BookForm, AuthorForm, AuthorFormSet

# トップページ
def index(request):
	return render(request, 'records/index.html')

# 入手記録一覧画面
def acquisition_list(request):
	# 動的にモデルのフィールドを取得
	model = AcquisitionRecord
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
	return render(request, 'records/acquisition_list.html', context)

# 入手記録詳細画面
def acquisition_detail(request, pk):
	record = get_object_or_404(AcquisitionRecord, pk=pk)
	
	items = record.items.all()
	# 各 item に対応する Book レコードを探して添付
	for item in items:
		if item.item_type == 'book' and item.item_id:
			item.book_record = Book.objects.filter(isbn=item.item_id).first()
		else:
			item.book_record = None
	
	context = {
		'record': record,
		'items': items,
		'acquisition_id': pk,
	}
	return render(request, 'records/acquisition_detail.html', context=context)

class AcquisitionEditView(TemplateView):
	template_name = 'records/acquisition_edit.html'
	
	def get(self, request, pk=None, *args, **kwargs):
		if pk:
			is_new_record = False
			acquisition = get_object_or_404(AcquisitionRecord, pk=pk)
			acquisition_form = AcquisitionForm(instance=acquisition)
			item_formset = AcquisitionItemFormSet(instance=acquisition)
			cancel_url = reverse('records:acquisition_detail', args=[pk])
		else:
			is_new_record = True
			acquisition_form = AcquisitionForm()
			item_formset = AcquisitionItemFormSet()
			cancel_url = reverse('records:acquisition_list')
		
		return render(request, self.template_name, context={
			'is_new_record': is_new_record,
			'PostSuccess': False,
			'acquisition_form': acquisition_form,
			'item_formset': item_formset,
			'item_columns': AcquiredItemForm.Meta.labels.values(),
			'cancel_url': cancel_url,
		})
	
	def post(self, request, pk=None):
		"""
		POSTリクエストの処理
		
		Args:
			request:

		Returns:

		"""
		if pk:
			is_new_record = False
			acquisition = get_object_or_404(AcquisitionRecord, pk=pk)
			acquisition_form = AcquisitionForm(request.POST, request.FILES, instance=acquisition)
			item_formset = AcquisitionItemFormSet(request.POST, request.FILES, instance=acquisition)
			cancel_url = reverse('records:acquisition_detail', args=[pk])
		else:
			is_new_record = True
			acquisition_form = AcquisitionForm(request.POST, request.FILES)
			item_formset = AcquisitionItemFormSet(request.POST, request.FILES)
			cancel_url = reverse('records:acquisition_list')
		
		context = {
			'is_new_record': is_new_record,
			'acquisition_form': acquisition_form,
			'item_formset': item_formset,
			'item_columns': AcquiredItemForm.Meta.labels.values(),
			'PostSuccess': False,
			'cancel_url': cancel_url,
		}
		
		if acquisition_form.is_valid() and item_formset.is_valid():
			# データ検証成功
			with transaction.atomic():  # データベース操作をアトミックに実行
				new_acquisition = acquisition_form.save()
				item_formset.instance = new_acquisition  # Formsetに親インスタンスを紐付け
				item_formset.save()
			
			# TODO: この処理が必要かどうか見直し
			# 成功時のフォームのクリア
			context['acquisition_form'] = AcquisitionForm()
			context['item_formset'] = AcquisitionItemFormSet()
			context['PostSuccess'] = True
			
			# 成功時のリダイレクトも検討する。例えば、新しい詳細ページや一覧ページへ
			return redirect(reverse_lazy('records:acquisition_detail', args=[new_acquisition.pk]))  # acquisition_success_pageは例
		else:
			# フォームが有効ではない場合、
			# エラーメッセージを表示するために現在のフォームをcontextに含める
			print(f"Errors: {acquisition_form.errors}")
			print(f"Item errors: {item_formset.errors}")
		
		return render(request, self.template_name, context=context)

def acquisition_delete(request, pk):
	record = get_object_or_404(AcquisitionRecord, pk=pk)
	if request.method == 'POST':
		record.delete()
		messages.success(request, f'「{record}」を削除しました。')
		return redirect(reverse_lazy('records:acquisition_list'))
	# GET で来たら詳細画面に戻す
	return redirect(
		record.get_absolute_url() if hasattr(record, 'get_absolute_url')
		else reverse_lazy('records:acquisition_detail', args=[pk])
	)

# 書籍一覧画面
def book_list(request):
	# 動的にモデルのフィールドを取得
	model = Book
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
	return render(request, 'records/book_list.html', context)

# 書籍詳細画面
def book_detail(request, pk):
	record = get_object_or_404(Book, pk=pk)
	authors = record.authors.all()
	context = {
		'record': record,
		'authors': authors,
		'book_id': pk,
	}
	return render(request, 'records/book_detail.html', context=context)

class BookEditView(TemplateView):
	template_name = 'records/book_edit.html'
	
	def get(self, request, pk=None, *args, **kwargs):
		if pk:
			# 既存レコードの再編集
			is_new_record = False
			book = get_object_or_404(Book, pk=pk)
			book_form = BookForm(instance=book)
			author_formset = AuthorFormSet(instance=book)
			cancel_url = reverse('records:book_detail', args=[pk])
		else:
			# 新規登録
			is_new_record = True
			
			# クエリの処理
			initial = { }
			if isbn_prefill := request.GET.get('isbn', ''):
				initial['isbn'] = isbn_prefill
			if title_prefill := request.GET.get('title', ''):
				initial['title'] = title_prefill
			
			book_form = BookForm(initial=initial)
			author_formset = AuthorFormSet()
			cancel_url = reverse('records:book_list')
		
		return render(request, self.template_name, context={
			'is_new_record': is_new_record,
			'PostSuccess': False,
			'book_form': book_form,
			'author_formset': author_formset,
			'author_columns': AuthorForm.Meta.labels.values(),
			'cancel_url': cancel_url,
		})
	
	def post(self, request, pk=None):
		"""
		POSTリクエストの処理

		Args:
			request:

		Returns:

		"""
		if pk:
			is_new_record = False
			book = get_object_or_404(Book, pk=pk)
			book_form = BookForm(request.POST, request.FILES, instance=book)
			author_formset = AuthorFormSet(request.POST, request.FILES, instance=book)
			cancel_url = reverse('records:book_detail', args=[pk])
		else:
			is_new_record = True
			book_form = BookForm(request.POST, request.FILES)
			author_formset = AuthorFormSet(request.POST, request.FILES)
			cancel_url = reverse('records:book_list')
		
		context = {
			'is_new_record': is_new_record,
			'PostSuccess': False,
			'book_form': book_form,
			'author_formset': author_formset,
			'author_columns': AuthorForm.Meta.labels.values(),
			'cancel_url': cancel_url,
		}
		
		if book_form.is_valid() and author_formset.is_valid():
			# データ検証成功
			with transaction.atomic():  # データベース操作をアトミックに実行
				new_book = book_form.save()
				author_formset.instance = new_book  # Formsetに親インスタンスを紐付け
				author_formset.save()
			
			# TODO: この処理が必要かどうか見直し
			# 成功時のフォームのクリア
			context['book_form'] = BookForm()
			context['author_formset'] = AuthorFormSet()
			context['PostSuccess'] = True
			
			# 成功時のリダイレクトも検討する。例えば、新しい詳細ページや一覧ページへ
			return redirect(reverse_lazy('records:book_detail', args=[new_book.pk]))
		else:
			# フォームが有効ではない場合、
			# エラーメッセージを表示するために現在のフォームをcontextに含める
			print(f"Errors: {book_form.errors}")
			print(f"Item errors: {author_formset.errors}")
		
		return render(request, self.template_name, context=context)

# 書籍情報編集画面
def book_delete(request):
	context = {
	}
	return render(request, 'records/book_edit.html', context=context)

# 統計画面
def stats(request):
	context = {
	}
	return render(request, 'records/stats.html', context=context)
