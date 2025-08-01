"""
livre_manager/records/urls.py
URL configuration for livre_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path

from . import views

BOOK_ID_TYPES = "isbn|jan|asin"
NANOID_PATTERN = r'[\w\-]{21}'

app_name = "records"
urlpatterns = [
	# トップページ
	path("", views.index, name="index"),
	# 入手記録一覧
	path("acquisition/", views.acquisition_list, name="acquisition_list"),
	# 入手記録の新規作成
	path("acquisition/new/", views.AcquisitionEditView.as_view(), name="acquisition_new"),
	# 入手記録詳細
	re_path(rf"acquisition/(?P<pk>{NANOID_PATTERN})/$", views.acquisition_detail, name="acquisition_detail"),
	# 入手記録編集
	re_path(rf"acquisition/(?P<pk>{NANOID_PATTERN})/edit/$", views.AcquisitionEditView.as_view(), name="acquisition_edit"),
	# 入手記録削除のエンドポイント
	re_path(rf"acquisition/(?P<pk>{NANOID_PATTERN})/delete/$", views.acquisition_delete, name="acquisition_delete"),
	# OCRエンドポイント
	path("acquisition/receipt_ocr/", views.receipt_ocr, name="receipt_ocr"),
	
	# 書籍一覧
	path("book/", views.book_list, name="book_list"),
	# 書籍の新規登録
	path("book/new/", views.BookEditView.as_view(), name="book_new"),
	# 書籍情報詳細
	re_path(rf"book/(?P<pk>{NANOID_PATTERN})/$", views.book_detail, name="book_detail"),
	re_path(r"book/isbn/(?P<pk>[a-zA-Z0-9]+)/$", views.book_detail, { "id_type": "isbn" }, name="book_detail_by_isbn"),  # ISBNをキーとする書籍情報詳細
	re_path(r"book/jan/(?P<pk>[a-zA-Z0-9]+)/$", views.book_detail, { "id_type": "jan" }, name="book_detail_by_jan"),  # JANをキーとする書籍情報詳細
	re_path(r"book/asin/(?P<pk>[a-zA-Z0-9]+)/$", views.book_detail, { "id_type": "asin" }, name="book_detail_by_asin"),  # ASINをキーとする書籍情報詳細
	# 書籍情報編集
	re_path(rf"book/(?P<pk>{NANOID_PATTERN})/edit/$", views.BookEditView.as_view(), name="book_edit"),
	# 書籍削除のエンドポイント
	re_path(rf"book/(?P<pk>{NANOID_PATTERN})/delete/$", views.book_delete, name="book_delete"),
	
	# 統計
	path("stats/", views.stats, name="stats"),
]

handler404 = views.page_not_found
