"""
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
from django.urls import path

from . import views

app_name = "records"
urlpatterns = [
	# ex: /polls/
	path("", views.index, name="index"),  # トップページ
	path("acquisition/", views.acquisition_list, name="acquisition_list"),  # 入手記録一覧
	path("acquisition/new", views.AcquisitionEditView.as_view(), name="acquisition_new"),  # 入手記録編集
	path("acquisition/<int:pk>", views.acquisition_detail, name="acquisition_detail"),  # 入手記録詳細
	path("acquisition/<int:pk>/edit", views.AcquisitionEditView.as_view(), name="acquisition_edit"),  # 入手記録編集
	path("acquisition/<int:pk>/delete", views.acquisition_delete, name="acquisition_delete"),  # 入手記録編集
	path("book/", views.book_list, name="book_list"),  # 書籍一覧
	path("book/new", views.BookEditView.as_view(), name="book_new"),  # 書籍一覧
	path("book/<str:pk>", views.book_detail, name="book_detail"),  # 書籍情報詳細
	path("book/<str:pk>/edit", views.BookEditView.as_view(), name="book_edit"),  # 書籍情報編集
	path("book/<str:pk>/delete", views.book_delete, name="book_delete"),  # 書籍情報編集
	path("stats/", views.stats, name="stats"),  # 統計
]
