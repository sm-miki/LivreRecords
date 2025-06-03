from datetime import datetime
from django.db import models

# Create your models here.


class ObtainRecord(models.Model):
	"""
	入手記録テーブルのフィールドを定義する。
	"""
	# 入手タイプ。
	OBTAIN_TYPE_CHOICES = [
		('purchase', '購入'),
		('other', 'その他'),
	]
	obtain_type = models.CharField(max_length=10, choices=OBTAIN_TYPE_CHOICES, default='purchase')
	# 店舗名
	store_name = models.TextField(null=False, blank=True)
	# 取得日時 (生文字列形式。正規化済み)
	obtain_date_str = models.TextField(null=False, blank=True)
	# 取得日時 (日時型)
	obtain_date = models.DateTimeField(null=True, blank=True)
	# 取引番号
	transaction_number = models.TextField(null=False, blank=True)
	# その他取引情報
	transaction_context = models.TextField(null=False, blank=True)
	# 担当者情報
	staff = models.TextField(null=False, blank=True)
	# 通貨単位
	NULL_CURRENCY_UNIT = ''
	JPY_UNIT = 'JPY'
	USD_UNIT = 'USD'
	CURRENCY_UNIT_CHOICES = (
		(NULL_CURRENCY_UNIT, u"---"),
		(JPY_UNIT, u"円"),
		(USD_UNIT, u"ドル(USD)"),
	)
	currency_unit = models.CharField(max_length=10, choices=CURRENCY_UNIT_CHOICES, blank=True, default=JPY_UNIT)
	
	# 合計支払金額
	total = models.IntegerField(null=True, blank=True)
	# 税抜金額
	subtotal = models.IntegerField(null=True, blank=True)
	# 税額
	tax = models.IntegerField(null=True, blank=True)
	
	# 支払い方法
	PAYMENT_METHOD_CHOICES = [
		('', '未選択'),
		('cash', '現金'),
		('credit', 'クレジットカード'),
	]
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
	
	def clean(self):
		if self.obtain_date_str:
			try:
				self.obtain_date = datetime.strptime(self.obtain_date_str, "%Y/%m/%d").date()
			except ValueError:
				self.obtain_date = None
	
	def __str__(self):
		return f"{self.obtain_date_str} {self.store_name}"
	
	class Meta:
		ordering = ["-created_at"]
		verbose_name = '入手情報'
		verbose_name_plural = '入手情報'

class ObtainedItem(models.Model):
	"""
	入手記録テーブルのフィールドを定義する。
	"""
	obtain_record = models.ForeignKey(ObtainRecord, on_delete=models.CASCADE, related_name='items')
	
	# 項目タイプ
	ITEM_TYPE_CHOICES = (
		('book', u"書籍"),
		('other', u"その他"),
	)
	item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='book')
	# 商品・書籍ID
	item_id = models.TextField(null=True, blank=True)
	# ジャンルコード
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
		return f"{self.item_type} - {self.item_id} ({self.obtain_record.obtain_date})"

	class Meta:
		ordering = ["-created_at"]
		verbose_name = '入手項目'
		verbose_name_plural = '入手項目'

class Book:
	# タイトル
	title = models.TextField()
	# シリーズ・レーベル名
	series = models.TextField()
	# ISBN
	isbn = models.TextField()
	# JANコード
	jan = models.TextField()
	# ASIN (Amazon標準商品番号)
	asin = models.TextField()
	# 出版社
	publisher = models.TextField()
	# 出版日
	publish_date_raw = models.TextField(null=True)
	# 出版日シリアル値
	publish_date = models.DateField(null=True)
	# 定価
	price = models.IntegerField()
	# 書影画像
	cover_image = models.ImageField()
	# ユーザーメモ
	user_memo = models.TextField()
	# 所有済みフラグ
	has_item = models.BooleanField()
	
	# レコード作成日時
	created_at = models.DateTimeField(auto_now_add=True)
	# レコード更新日時
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f"{self.isbn} {self.title}"

class BookAuthorRelation:
	# 書籍ID
	book_id = models.IntegerField()
	# 記載順
	order = models.IntegerField()
	# 著者名
	author_name = models.TextField()
	# 役割
	role = models.TextField()
	
	# レコード作成日時
	created_at = models.DateTimeField(auto_now_add=True)
	# レコード更新日時
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f"{self.book_id} {self.author_name}"
