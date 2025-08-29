"""
records/views.py
"""
from typing import Optional
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q, F
from django.db.models import Count, Case, When, Value, IntegerField, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime, date, timedelta  # datetime, date, timedelta をインポート
from django.utils import timezone  # タイムゾーン対応のためにtimezoneをインポート

from .currency import CURRENCY_INFO
from .receipt_reader import ReceiptReader
from .receipt_reader.ocr_engine import EasyOCREngine
from . import book_utils

from .models import Acquisition, Book, AcquiredItem
from .acquisition_form import AcquisitionForm, AcquiredItemForm, AcquisitionItemFormSet
from .book_form import BookForm, AuthorForm, AuthorFormSet

def index(request):
	"""
	トップページ
	"""
	today = timezone.localdate()
	recent_acquisitions = Acquisition.objects.order_by('-updated_at')[:5]
	# 近日発売の書籍一覧
	upcoming_books = Book.objects.filter(
		publication_date__gte=today,
		publication_date__lte=today + timedelta(days=14)
	).order_by('publication_date')
	# 近日発売の書籍一覧
	recent_books = Book.objects.filter(
		publication_date__gte=today - timedelta(days=14),
		publication_date__lte=today
	).order_by('publication_date')
	
	return render(request, 'records/index.html', {
		'recent_acquisitions': recent_acquisitions,
		'recent_books': recent_books,
		'upcoming_books': upcoming_books,
	})

def acquisition_list(request):
	"""
	入手記録の一覧表示を行うビュー。
	"""
	# 動的にモデルのフィールドを取得
	model = Acquisition
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

def acquisition_detail(request, pk):
	"""
	入手記録の詳細表示を行うビュー。
	"""
	record = get_object_or_404(Acquisition, pk=pk)
	
	items = record.items.all()
	# 書籍アイテムに対応するBookレコードを一括で取得して紐付ける (N+1問題対策)
	book_isbns = [item.item_id for item in items if item.item_type == 'book' and item.item_id]
	books_by_isbn = { }
	if book_isbns:
		books = Book.objects.filter(isbn__in=book_isbns)
		books_by_isbn = { book.isbn: book for book in books }
	
	for item in items:
		item.book_record = books_by_isbn.get(item.item_id) if item.item_type == 'book' else None
	
	context = {
		'record': record,
		'items': items,
		'acquisition_id': pk,
	}
	return render(request, 'records/acquisition_detail.html', context=context)

class AcquisitionEditView(TemplateView):
	"""
	入手記録の編集を行うビュー。
	新規登録と再編集の両方を同じ画面で処理する。
	"""
	template_name = 'records/acquisition_edit.html'
	
	def get(self, request, pk=None, *args, **kwargs):
		if pk:
			is_new_record = False
			acquisition = get_object_or_404(Acquisition, pk=pk)
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
			acquisition = get_object_or_404(Acquisition, pk=pk)
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
			# データ検証成功 => データベースに書き込み
			with transaction.atomic():  # データベース操作をアトミックに実行
				new_acquisition = acquisition_form.save()
				item_formset.instance = new_acquisition  # Formsetに親インスタンスを紐付け
				item_formset.save()
			
			messages.success(request, f'入手記録「{new_acquisition}」を保存しました。')
			return redirect(reverse_lazy('records:acquisition_detail', args=[new_acquisition.pk]))
		else:
			# フォームが有効ではない場合、
			# エラーメッセージを表示するために現在のフォームをcontextに含める
			print(f"Errors: {acquisition_form.errors}")
			print(f"Item errors: {item_formset.errors}")
		
		return render(request, self.template_name, context=context)

def acquisition_delete(request, pk):
	"""
	入手記録の削除を行うAPIエントリ。
	"""
	record = get_object_or_404(Acquisition, pk=pk)
	if request.method == 'POST':
		record.delete()
		messages.success(request, f'「{record}」を削除しました。')
		return redirect(reverse_lazy('records:acquisition_list'))
	
	# GET で来たら詳細画面に戻す
	return redirect(
		record.get_absolute_url() if hasattr(record, 'get_absolute_url')
		else reverse_lazy('records:acquisition_detail', args=[pk])
	)

# レシート読み取りのエンドポイント
@csrf_exempt
def receipt_ocr(request):
	"""
	レシート画像の解析を行うAPIエントリ。
	"""
	if request.method == 'POST' and request.FILES.get('receipt_image'):
		uploaded_image = request.FILES['receipt_image']
		
		try:
			# Pass the image to your ReceiptReader
			# Assuming ReceiptReader.read_receipt returns a dictionary with 'isbns' list
			reader = ReceiptReader(EasyOCREngine())
			preprocess_types = [
				# ('crop', { 'size_scale': (1.0, 1.0) }),
				('greyscale', { }),
				('unsharp_masking', { 'alpha': 1.6 }),
			]
			receipt_data = reader.read_receipt(uploaded_image.read(), preprocess_type=preprocess_types).receipt_data
			
			return JsonResponse({ 'success': True, 'receipt': receipt_data })
		except Exception as e:
			# Log the error for debugging
			print(f"Error processing receipt image: {e}")
			return JsonResponse({ 'success': False, 'message': 'Error processing image.' }, status=500)
	
	return JsonResponse({ 'success': False, 'message': 'Invalid request.' }, status=400)

# 書籍一覧画面
def book_list(request):
	"""
	書籍情報の一覧表示を行うビュー。
	"""
	# 動的にモデルのフィールドを取得
	model = Book
	fields = [f for f in model._meta.fields if f.name not in model.READONLY_FIELDS]
	
	# フィールド名とヘッダー用ラベルを準備
	headers = [f.verbose_name for f in fields]
	field_names = [f.name for f in fields]
	
	# 全レコードを取得
	records = model.objects.all().prefetch_related('authors')
	
	context = {
		'headers': headers,
		'field_names': field_names,
		'records': records,
	}
	return render(request, 'records/book_list.html', context)

def book_detail(request, pk: str, id_type=None):
	"""
	書籍情報の詳細表示を行うビュー。
	"""
	if id_type:
		match id_type.lower():
			case 'isbn':
				record = get_object_or_404(Book, isbn=pk)
			case 'jan':
				record = get_object_or_404(Book, jan=pk)
			case 'asin':
				record = get_object_or_404(Book, asin=pk)
	else:
		record = get_object_or_404(Book, pk=pk)
	
	authors = record.authors.all()
	
	# この書籍を含む入手記録を取得
	related_acquisitions = []
	if record.isbn:
		acquisition_ids = AcquiredItem.objects.filter(
			item_type='book',
			item_id=record.isbn
		).values_list('acquisition_id', flat=True).distinct()
		related_acquisitions = Acquisition.objects.filter(
			pk__in=acquisition_ids
		).order_by('-acquisition_date')
	
	# 外部リンク
	if record.isbn:
		external_links = list(book_utils.get_external_links(record.isbn).values())
	else:
		external_links = []
	
	context = {
		'record': record,
		'authors': authors,
		'book_id': pk,
		'related_acquisitions': related_acquisitions,
		'external_links': external_links,
	}
	return render(request, 'records/book_detail.html', context=context)

class BookEditView(TemplateView):
	"""
	書籍情報の編集を行うビュー。
	新規登録と再編集の両方を同じ画面で処理する。
	"""
	template_name = 'records/book_edit.html'
	
	def get(self, request, pk: Optional[str] = None, *args, **kwargs):
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
			# book = Book()
			# book_form = BookForm(initial=initial, instance=book)
			# author_formset = AuthorFormSet(
			# 	instance=book,
			# 	queryset=BookAuthorRelation.objects.none()
			# )
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
			# 再編集の場合
			is_new_record = False
			book = get_object_or_404(Book, pk=pk)
			book_form = BookForm(request.POST, request.FILES, instance=book)
			author_formset = AuthorFormSet(request.POST, request.FILES, instance=book)
			cancel_url = reverse('records:book_detail', args=[pk])
		else:
			# 新規作成の場合
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
			
			messages.success(request, f'書籍「{new_book}」を保存しました。')
			return redirect(reverse_lazy('records:book_detail', args=[new_book.pk]))
		else:
			# フォームが有効ではない場合、
			# エラーメッセージを表示するために現在のフォームをcontextに含める
			print(f"Errors: {book_form.errors}")
			print(f"Item errors: {author_formset.errors}")
		
		return render(request, self.template_name, context=context)

def book_delete(request, pk):
	"""
	書籍情報の削除を行うエントリ。
	"""
	record = get_object_or_404(Book, pk=pk)
	if request.method == 'POST':
		record.delete()
		messages.success(request, f'「{record}」を削除しました。')
		return redirect(reverse_lazy('records:book_list'))
	
	# GET で来たら詳細画面に戻す
	return redirect(
		record.get_absolute_url() if hasattr(record, 'get_absolute_url')
		else reverse_lazy('records:book_detail', args=[pk])
	)

# 統計画面
def stats(request):
	"""
	入手記録および書籍一覧の統計情報を表示するビュー。
	"""
	today = timezone.localdate()
	start_of_this_month = today.replace(day=1)
	# Django 4.1+ and Python 3.9+ can use calendar.monthrange
	import calendar
	_, last_day_of_month = calendar.monthrange(today.year, today.month)
	end_of_this_month = today.replace(day=last_day_of_month)
	
	this_month_q = Q(acquisition_date__range=(start_of_this_month, end_of_this_month))
	this_month_items_q = Q(acquisition__acquisition_date__range=(start_of_this_month, end_of_this_month))
	
	"""
	入手記録に基づく集計
	"""
	acquisition_stats = Acquisition.objects.aggregate(
		total_records=Count('id'),
		this_month_records=Count('id', filter=this_month_q)
	)
	
	item_stats = AcquiredItem.objects.filter(item_type='book').aggregate(
		total_purchase_count=Coalesce(Sum('quantity', filter=Q(acquisition__acquisition_type='purchase')), 0),
		this_month_purchase_count=Coalesce(Sum('quantity', filter=Q(acquisition__acquisition_type='purchase') & this_month_items_q), 0),
		total_other_count=Coalesce(Sum('quantity', filter=Q(acquisition__acquisition_type='other')), 0),
		this_month_other_count=Coalesce(Sum('quantity', filter=Q(acquisition__acquisition_type='other') & this_month_items_q), 0),
	)
	
	total_acquired_book_count = item_stats['total_purchase_count'] + item_stats['total_other_count']
	this_month_total_acquired_book_count = item_stats['this_month_purchase_count'] + item_stats['this_month_other_count']
	
	"""
	通貨別の集計
	"""
	currency_stats_query = AcquiredItem.objects.filter(
		item_type='book',
		price__isnull=False,
		quantity__isnull=False
	).values('acquisition__currency_code').annotate(
		total_book_count=Sum('quantity'),
		total_amount=Sum(F('price') * F('quantity')),
		this_month_book_count=Coalesce(Sum('quantity', filter=this_month_items_q), 0),
		this_month_total_amount=Coalesce(Sum(F('price') * F('quantity'), filter=this_month_items_q), 0, output_field=DecimalField())
	).order_by('acquisition__currency_code')
	
	currency_stats = { }
	for stat in currency_stats_query:
		code = stat['acquisition__currency_code']
		if not code:
			continue
		info = CURRENCY_INFO.get(code)
		if not info:
			continue
		
		total_book_count = stat['total_book_count']
		this_month_book_count = stat['this_month_book_count']
		total_amount = stat['total_amount']
		this_month_total_amount = stat['this_month_total_amount']
		
		currency_stats[code] = {
			'label': info['label'],
			'symbol': info['symbol'],
			'total_book_count': total_book_count,
			'total_amount': total_amount,
			'average_price': total_amount / total_book_count if total_book_count > 0 else 0,
			'this_month_book_count': this_month_book_count,
			'this_month_total_amount': this_month_total_amount,
			'this_month_average_price': this_month_total_amount / this_month_book_count if this_month_book_count > 0 else None,
		}
	
	"""
	書籍一覧の集計
	"""
	book_stats = Book.objects.aggregate(
		total_registered=Count('id'),
		owned_count=Count('id', filter=Q(has_item=True))
	)
	
	context = {
		'this_month': today.month,
		'total_acquisition_records': acquisition_stats['total_records'],
		'this_month_total_acquisition_records': acquisition_stats['this_month_records'],
		'purchase_book_count': item_stats['total_purchase_count'],
		'this_month_purchase_book_count': item_stats['this_month_purchase_count'],
		'other_acquisition_book_count': item_stats['total_other_count'],
		'this_month_other_acquisition_book_count': item_stats['this_month_other_count'],
		'total_acquired_book_count': total_acquired_book_count,
		'this_month_total_acquired_book_count': this_month_total_acquired_book_count,
		'currency_stats': currency_stats,
		'total_registered_books': book_stats['total_registered'],
		'owned_books_count': book_stats['owned_count'],
	}
	
	return render(request, f'records/stats.html', context=context)

def page_not_found(request, exception):
	"""
	カスタム404エラーページを表示するビュー。
	"""
	
	return render(request, 'records/404.html', status=404)
