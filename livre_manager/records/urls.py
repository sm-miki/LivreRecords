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
	path("obtains/", views.obtains, name="obtains"),  # 入手記録一覧
	path("obtain-edit", views.ObtainEditView.as_view(), name="obtain_edit"),  # 入手記録編集
	path("obtain/<str:pk>", views.obtain_detail, name="obtain_detail"),  # 入手記録詳細
	path("items/", views.items, name="items"),  # 書籍一覧
	path("item-edit", views.item_edit, name="item_edit"),  # 書籍情報編集
	path("item/<str:pk>", views.item_detail, name="item_detail"),  # 書籍情報詳細
	path("stats/", views.stats, name="stats"),  # 統計
]
