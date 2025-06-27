"""
records/models.py
"""
from datetime import datetime
from django.db import models
import dateutil.parser

# Create your models here.

default_date = datetime(1, 1, 1)

def validate_datetime(s):
	return dateutil.parser.parse(s, default=default_date)

class AcquisitionRecord(models.Model):
	"""
	入手記録テーブルのフィールドを定義する。
	"""
	# 入手タイプ。
	ACQUISITION_TYPE_CHOICES = {
		'purchase': '購入',
		'other': 'その他',
	}
	acquisition_type = models.CharField(max_length=10, choices=ACQUISITION_TYPE_CHOICES, default='purchase')
	# 取得日時 (生文字列形式。正規化済み)
	acquisition_date_str = models.TextField(null=False, blank=True)
	# 取得日時 (日時型)
	acquisition_date = models.DateTimeField(null=True, blank=True)
	# 店舗名
	store_name = models.TextField(null=False, blank=True)
	# 取引番号
	transaction_number = models.TextField(null=False, blank=True)
	# その他取引情報
	transaction_context = models.TextField(null=False, blank=True)
	# 担当者情報
	staff = models.TextField(null=False, blank=True)
	# 通貨単位
	NULL_CURRENCY_CODE = ''
	JPY = 'JPY'
	USD = 'USD'
	
	CURRENCY_CODE_CHOICES = {
		NULL_CURRENCY_CODE: u"---",
		JPY: u"円",
		USD: u"ドル(USD)",
	}
	currency_code = models.CharField(max_length=10, choices=CURRENCY_CODE_CHOICES, blank=True, default=JPY)
	
	# 合計支払金額
	total = models.IntegerField(null=True, blank=True)
	# 税抜金額
	subtotal = models.IntegerField(null=True, blank=True)
	# 税額
	tax = models.IntegerField(null=True, blank=True)
	# その他費用 (送料など)
	extra_fee = models.IntegerField(null=True, blank=True, default=0)
	
	# 支払い方法
	PAYMENT_METHOD_CHOICES = {
		'': '未指定',
		'cash': '現金',
		'credit': 'クレジットカード',
	}
	payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, blank=True, default='')
	
	# レシート画像
	receipt_image = models.ImageField(null=True, blank=True)
	# レシート画像 (切り抜き後)
	receipt_image_cropped = models.ImageField(null=True, blank=True)
	
	# レコード作成日時
	created_at = models.DateTimeField(auto_now_add=True)
	# レコード更新日時
	updated_at = models.DateTimeField(auto_now=True)
	
	READONLY_FIELDS = (
		'created_at', 'updated_at',
	)
	
	def acquisition_type_label(self):
		return self.ACQUISITION_TYPE_CHOICES[self.acquisition_type]
	
	def payment_method_label(self):
		return self.PAYMENT_METHOD_CHOICES[self.payment_method]
	
	@property
	def total_quantity(self):
		return sum(item.quantity for item in self.items.all())
	
	def clean(self):
		if self.acquisition_date_str:
			try:
				self.acquisition_date = validate_datetime(self.acquisition_date_str)
			except ValueError:
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
	acquisition_record = models.ForeignKey(
		AcquisitionRecord, on_delete=models.CASCADE, related_name='items'
	)
	
	# 項目タイプ
	ITEM_TYPE_CHOICES = {
		'book': u"書籍",
		'other': u"その他",
	}
	item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='book')
	# 商品・書籍ID
	item_id = models.TextField(null=True, blank=True)
	# 分類
	genre_code = models.TextField(blank=True)
	# 商品名・説明
	description = models.TextField(blank=True)
	# 税込価格
	price = models.IntegerField(null=True, blank=True)
	# 税抜価格
	net_price = models.IntegerField(null=True, blank=True)
	# 税額 (税込小計の場合)
	tax = models.IntegerField(null=True, blank=True)
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
		return f"{self.item_type}: {self.item_id} - {self.description} ({self.acquisition_record})"
	
	class Meta:
		ordering = ["-created_at"]
		verbose_name = '入手項目'
		verbose_name_plural = '入手項目'
	
	def item_type_label(self):
		return self.ITEM_TYPE_CHOICES[self.item_type]

class Book(models.Model):
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
	# 出版日
	publication_date_str = models.TextField(null=True, blank=True)
	# 出版日シリアル値
	publication_date = models.DateField(null=True, blank=True)
	# 定価
	price = models.IntegerField(null=True, blank=True)
	# 書影画像
	cover_image = models.ImageField(null=True, blank=True)
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
	
	def __str__(self):
		return f"{self.isbn} {self.title}"
	
	class Meta:
		ordering = ["-created_at"]
		verbose_name = '書籍'
		verbose_name_plural = '書籍'
	
	def clean(self):
		if self.has_item is None:
			self.has_item = False

class BookAuthorRelation(models.Model):
	book_record = models.ForeignKey(
		Book, on_delete=models.CASCADE, related_name='authors'
	)
	
	# # 記載順
	# order = models.IntegerField(null=False, blank=True)
	# 著者名
	author_name = models.TextField()
	# 役割
	role = models.TextField(null=True, blank=True)
	
	# レコード作成日時
	created_at = models.DateTimeField(auto_now_add=True)
	# レコード更新日時
	updated_at = models.DateTimeField(auto_now=True)
	
	READONLY_FIELDS = (
		'created_at', 'updated_at',
	)
	
	def __str__(self):
		return f"{self.author_name} {self.role} ({self.book_record.id} {self.book_record.title})"
	
	class Meta:
		ordering = ["-created_at"]
		verbose_name = '著者'
		verbose_name_plural = '著者'
