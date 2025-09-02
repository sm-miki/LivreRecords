"""
records/models.py
"""
import uuid
from datetime import datetime
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.urls import reverse
from django.dispatch import receiver
import dateutil.parser

from . import book_utils
from .unique_id_field import NanoIDField
from .currency import CURRENCY_CODE_CHOICES, JPY
from .fuzzy_datetime import FuzzyDatetime
from .fuzzy_datetime.error import FDError
from .tzutil import ALL_TIMEZONE_DATA, get_tzinfo, format_utcoffset

TIMEZONE_MAP = {
	name: d['name_with_offset'] for name, d in ALL_TIMEZONE_DATA.items()
}

default_date = datetime(1, 1, 1)

def validate_datetime(s):
	return dateutil.parser.parse(s, default=default_date)

class Acquisition(models.Model):
	"""
	入手記録テーブルのフィールドを定義する。
	"""
	
	# NanoIDキー
	id = NanoIDField(primary_key=True, help_text="レコードID")
	
	# 入手タイプ
	ACQUISITION_TYPE_CHOICES = {
		'purchase': '購入',
		'other': 'その他',
	}
	acquisition_type = models.CharField(
		max_length=10,
		choices=ACQUISITION_TYPE_CHOICES,
		default='purchase',
		verbose_name='入手タイプ',
		help_text='入手方法（購入/その他）',
	)
	# 取得日時
	acquisition_date_str = models.TextField(
		null=False,
		blank=True,
		verbose_name='取得日時（文字列）',
		help_text='取得日時を文字列で記録'
	)
	acquisition_date_tz = models.CharField(
		max_length=40,
		choices=TIMEZONE_MAP,
		default='Asia/Tokyo',
		verbose_name='取得日時タイムゾーン',
		help_text='取得日時のタイムゾーン（例: Asia/Tokyo）',
	)
	acquisition_date = models.DateTimeField(
		null=True,
		blank=True,
		verbose_name='取得日時',
		help_text='取得日時（日時型）'
	)
	# 店舗名
	store_name = models.TextField(
		null=False,
		blank=True,
		verbose_name='店舗名',
		help_text='購入・取得した店舗名'
	)
	# 取引番号
	transaction_number = models.TextField(
		null=False,
		blank=True,
		verbose_name='取引番号',
		help_text='取引番号やレシート番号'
	)
	# その他取引情報
	transaction_context = models.TextField(
		null=False,
		blank=True,
		verbose_name='取引情報',
		help_text='その他の取引に関する情報'
	)
	# 担当者情報
	staff = models.TextField(
		null=False,
		blank=True,
		verbose_name='担当者',
		help_text='担当スタッフ名'
	)
	# 通貨単位
	currency_code = models.CharField(
		max_length=10,
		choices=CURRENCY_CODE_CHOICES,
		blank=True,
		default=JPY,
		verbose_name='通貨単位',
		help_text='支払いに使用した通貨'
	)
	
	# 合計支払金額
	total = models.DecimalField(
		null=True,
		blank=True,
		verbose_name='合計支払金額',
		help_text='支払った合計金額（税込）',
		max_digits=9,
		decimal_places=3,
	)
	# 税抜金額
	subtotal = models.DecimalField(
		null=True,
		blank=True,
		verbose_name='税抜金額',
		help_text='税抜の合計金額',
		max_digits=9,
		decimal_places=3,
	)
	# 税額
	tax = models.DecimalField(
		null=True,
		blank=True,
		verbose_name='税額',
		help_text='消費税額',
		max_digits=9,
		decimal_places=3,
	)
	# その他費用 (送料など)
	extra_fee = models.DecimalField(
		null=True,
		blank=True,
		verbose_name='その他費用',
		help_text='送料など追加費用',
		max_digits=9,
		decimal_places=3,
	)
	
	# 支払い方法
	PAYMENT_METHOD_CHOICES = {
		'': '未指定',
		'cash': '現金',
		'credit': 'クレジットカード',
	}
	payment_method = models.CharField(
		max_length=10,
		choices=PAYMENT_METHOD_CHOICES,
		blank=True,
		default='',
		verbose_name='支払い方法',
		help_text='現金・クレジットカード等'
	)
	
	# レシート画像
	receipt_image = models.ImageField(
		null=True,
		blank=True,
		upload_to='receipts/',
		verbose_name='レシート画像',
		help_text='レシートの画像ファイル'
	)
	# レシート画像 (切り抜き後)
	receipt_image_cropped = models.ImageField(
		null=True,
		blank=True,
		verbose_name='レシート画像（切り抜き）',
		help_text='切り抜き済みレシート画像'
	)
	
	# レコード作成・更新日時（管理用）
	created_at = models.DateTimeField(
		auto_now_add=True,
		verbose_name='作成日時',
		help_text='レコード作成日時'
	)
	updated_at = models.DateTimeField(
		auto_now=True,
		verbose_name='更新日時',
		help_text='レコード更新日時'
	)
	
	READONLY_FIELDS = (
		'created_at', 'updated_at',
	)
	
	def acquisition_type_label(self):
		return self.ACQUISITION_TYPE_CHOICES[self.acquisition_type]
	
	def payment_method_label(self):
		return self.PAYMENT_METHOD_CHOICES[self.payment_method]
	
	def acquisition_date_info(self):
		if self.acquisition_date is None:
			return None
		
		tzinfo = get_tzinfo(self.acquisition_date_tz)
		dt = self.acquisition_date.astimezone(tzinfo)
		tz_abbr = dt.strftime('%Z')
		if tz_abbr[0] in ('+', '-'):
			tz_abbr = 'UTC' + tz_abbr
		tz_name = tzinfo.tzname(None)
		tz_offset = format_utcoffset(dt.utcoffset().total_seconds())
		
		return {
			'tz_name': tz_name,
			'tz_abbr': tz_abbr,
			'tz_offset': tz_offset,
		}
	
	@property
	def total_quantity(self):
		return sum(item.quantity for item in self.items.all())
	
	def clean(self):
		# 入手日時文字列の検証と正規化
		if self.acquisition_date_str:
			try:
				dt = FuzzyDatetime.parse(self.acquisition_date_str, precision_required='day')
				try:
					self.acquisition_date_str = dt.to_string(tz_formats='none')
				except FDError:
					pass
				
				self.acquisition_date = dt.to_datetime().astimezone(get_tzinfo(self.acquisition_date_tz))
			except FDError:
				self.acquisition_date = None
				raise
	
	def __str__(self):
		return f"{self.acquisition_date_str or 'NoneDate'} @ {self.store_name}"
	
	class Meta:
		ordering = ["-created_at"]
		verbose_name = '入手情報'
		verbose_name_plural = '入手情報'

class AcquiredItem(models.Model):
	"""
	入手記録テーブルのフィールドを定義する。
	"""
	acquisition = models.ForeignKey(
		Acquisition, on_delete=models.CASCADE, related_name='items',
		null=False, blank=False,
	)
	order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
	
	# 項目タイプ
	ITEM_TYPE_CHOICES = {
		'book': u"書籍",
		'other': u"その他",
	}
	item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='book')
	
	# 書籍識別ID（ISBNなど）
	item_id = models.TextField(null=True, blank=True)
	# 分類
	genre_code = models.TextField(blank=True)
	# 商品名・説明
	description = models.TextField(blank=True)
	# 税込価格
	price = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=3)
	# 税抜価格
	net_price = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=3)
	# 税額 (税込小計の場合)
	tax = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=3)
	# 数量
	quantity = models.IntegerField(null=True, blank=True, default=1)
	# ユーザーメモ
	user_memo = models.TextField(blank=True)
	
	# レコード作成日時
	created_at = models.DateTimeField(auto_now_add=True)
	# レコード更新日時
	updated_at = models.DateTimeField(auto_now=True)
	
	READONLY_FIELDS = (
		'created_at', 'updated_at',
	)
	
	def __str__(self):
		return f"{self.item_type}: {self.item_id} - {self.description} ({self.acquisition})"
	
	class Meta:
		ordering = ['order']
		verbose_name = '入手項目'
		verbose_name_plural = '入手項目'
	
	def item_type_label(self):
		return self.ITEM_TYPE_CHOICES[self.item_type]

class Book(models.Model):
	id = NanoIDField(primary_key=True, help_text="レコードID")
	
	# タイトル
	title = models.TextField()
	# シリーズ・レーベル名
	series = models.TextField(null=True, blank=True)
	# ISBN
	isbn = models.TextField(null=True, blank=True)
	# JANコード
	jan = models.TextField(null=True, blank=True)
	# ASIN (Amazon標準商品番号)
	asin = models.TextField(null=True, blank=True)
	# 出版社
	publisher = models.TextField(null=True, blank=True)
	# 発売日
	publication_date_str = models.TextField(null=True, blank=True)
	# 出版日シリアル値
	publication_date = models.DateField(null=True, blank=True)
	# 定価
	price = models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=3)
	# 通貨単位
	currency_code = models.CharField(max_length=10, choices=CURRENCY_CODE_CHOICES, blank=True, default=JPY)
	# 書影画像
	cover_image = models.ImageField(null=True, blank=True, upload_to='covers/')
	# ユーザーメモ
	user_memo = models.TextField(null=False, blank=True)
	# 所有済みフラグ
	has_item = models.BooleanField(null=False, blank=True)
	
	# レコード作成日時
	created_at = models.DateTimeField(auto_now_add=True)
	# レコード更新日時
	updated_at = models.DateTimeField(auto_now=True)
	
	READONLY_FIELDS = (
		'created_at', 'updated_at',
	)
	
	@property
	def isbn10(self):
		"""
		ISBN-13をISBN-10に変換して返す。
		ISBNがISBN-10に変換できない形式の場合はNoneを返す。
		"""
		if not self.isbn:
			return None
		
		if len(self.isbn) == 10:
			return self.isbn
		
		if len(self.isbn) == 13:
			try:
				return book_utils.isbn13_to_isbn10(self.isbn)
			except ValueError:
				return None
		return None
	
	@property
	def permalink(self):
		return reverse('records:book_detail', kwargs={ 'pk': self.id })
	
	def __str__(self):
		return f"{self.isbn} {self.title}"
	
	class Meta:
		ordering = ["-created_at"]
		verbose_name = '書籍'
		verbose_name_plural = '書籍'
	
	def clean(self):
		if self.has_item is None:
			self.has_item = False
		
		if self.isbn:
			self.isbn = self.isbn.replace('-', '')
		
		# 入手日時文字列の検証と正規化
		if self.publication_date_str:
			try:
				dt = FuzzyDatetime.parse_date(self.publication_date_str, precision_required='year')
				try:
					self.publication_date_str = dt.to_string()
				except FDError:
					pass
				
				self.publication_date = dt.to_datetime()
			except FDError:
				self.publication_date = None
				raise

class BookAuthorRelation(models.Model):
	book_record = models.ForeignKey(
		Book, on_delete=models.CASCADE, related_name='authors',
		null=False, blank=False,
	)
	
	# 対応するBook内での記載順
	order = models.PositiveIntegerField(default=0, null=False, blank=True)
	# 著者名
	author_name = models.TextField()
	# 役割
	role = models.TextField(null=True, blank=True)
	
	# レコード作成日時
	created_at = models.DateTimeField(auto_now_add=True)
	# レコード更新日時
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f"{self.author_name} {self.role} ({self.book_record.isbn} - {self.book_record.title})"
	
	class Meta:
		ordering = ['order']
		verbose_name = '著者'
		verbose_name_plural = '著者'
