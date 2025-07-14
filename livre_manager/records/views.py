"""
records/views.py
"""
import json
from django.db import transaction
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q, F
from datetime import datetime, date, timedelta  # datetime, date, timedelta をインポート
from django.utils import timezone  # タイムゾーン対応のためにtimezoneをインポート

from .receipt_reader import ReceiptReader
from .receipt_reader.ocr_engine import EasyOCREngine

from .models import Acquisition, Book, AcquiredItem
from .acquisition_form import AcquisitionForm, AcquiredItemForm, AcquisitionItemFormSet
from .book_form import BookForm, AuthorForm, AuthorFormSet

def index(request):
	"""
	トップページ
	"""
	recent_acquisitions = Acquisition.objects.order_by('-updated_at')[:5]
	# 近日発売の書籍一覧
	upcoming_books = Book.objects.filter(
		publication_date__gte=date.today(),
		publication_date__lte=date.today() + timedelta(days=14)
	).order_by('publication_date')
	# 近日発売の書籍一覧
	recent_books = Book.objects.filter(
		publication_date__gte=date.today() - timedelta(days=14),
		publication_date__lte=date.today()
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

def book_detail(request, pk):
	"""
	書籍情報の詳細表示を行うビュー。
	"""
	record = get_object_or_404(Book, pk=pk)
	authors = record.authors.all()
	context = {
		'record': record,
		'authors': authors,
		'book_id': pk,
	}
	return render(request, 'records/book_detail.html', context=context)

class BookEditView(TemplateView):
	"""
	書籍情報の編集を行うビュー。
	新規登録と再編集の両方を同じ画面で処理する。
	"""
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
	
	if start_of_this_month.month == 12:
		next_month_start = start_of_this_month.replace(year=start_of_this_month.year + 1, month=1, day=1)
	else:
		next_month_start = start_of_this_month.replace(month=start_of_this_month.month + 1, day=1)
	end_of_this_month = next_month_start - timedelta(days=1)
	
	this_month_acquisitions = Acquisition.objects.filter(
		acquisition_date__range=(start_of_this_month, end_of_this_month)
	)
	this_month_acquired_items = AcquiredItem.objects.filter(
		acquisition__acquisition_date__range=(start_of_this_month, end_of_this_month)
	)
	
	# 購入記録数
	total_acquisition_records = Acquisition.objects.count()
	this_month_total_acquisition_records = this_month_acquisitions.count()
	
	# 購入点数の集計
	purchase_book_count = AcquiredItem.objects.filter(
		acquisition__acquisition_type='purchase',
		item_type='book'
	).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
	this_month_purchase_book_count = this_month_acquired_items.filter(
		acquisition__acquisition_type='purchase',
		item_type='book'
	).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
	
	# その他入手点数の集計
	other_acquisition_book_count = AcquiredItem.objects.filter(
		acquisition__acquisition_type='other',
		item_type='book'
	).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
	this_month_other_acquisition_book_count = this_month_acquired_items.filter(
		acquisition__acquisition_type='other',
		item_type='book'
	).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
	
	# 合計入手点数の集計
	total_acquired_book_count = purchase_book_count + other_acquisition_book_count
	this_month_total_acquired_book_count = this_month_purchase_book_count + this_month_other_acquisition_book_count
	
	# 購入金額の合計
	purchase_total_amount = AcquiredItem.objects.filter(
		item_type='book',
		price__isnull=False,  # priceがnullでないことを確認
		quantity__isnull=False  # quantityがnullでないことを確認
	).aggregate(
		total_sum=Sum(F('price') * F('quantity'))  # priceとquantityの積を合計
	)['total_sum'] or 0
	this_month_purchase_total_amount = this_month_acquired_items.filter(
		item_type='book',
		price__isnull=False,  # priceがnullでないことを確認
		quantity__isnull=False  # quantityがnullでないことを確認
	).aggregate(
		total_sum=Sum(F('price') * F('quantity'))  # priceとquantityの積を合計
	)['total_sum'] or 0
	
	# 書籍の登録冊数 (Bookモデルの全レコード数)
	total_registered_books = Book.objects.count()
	
	# 所有済み冊数 (Bookモデルのhas_itemがTrueのレコード数)
	owned_books_count = Book.objects.filter(has_item=True).count()
	
	context = {
		'total_acquisition_records': total_acquisition_records,
		'this_month_total_acquisition_records': this_month_total_acquisition_records,
		'purchase_book_count': purchase_book_count,
		'this_month_purchase_book_count': this_month_purchase_book_count,
		'other_acquisition_book_count': other_acquisition_book_count,
		'this_month_other_acquisition_book_count': this_month_other_acquisition_book_count,
		'total_acquired_book_count': total_acquired_book_count,
		'this_month_total_acquired_book_count': this_month_total_acquired_book_count,
		'purchase_total_amount': purchase_total_amount,
		'this_month_purchase_total_amount': this_month_purchase_total_amount,
		'total_registered_books': total_registered_books,
		'owned_books_count': owned_books_count,
	}
	
	return render(request, 'records/stats.html', context=context)
