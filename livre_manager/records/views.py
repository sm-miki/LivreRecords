from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

# トップページ
def index(request):
	return render(request, 'records/index.html')

# 入手記録一覧画面
def obtains(request):
	return render(request, 'records/obtains.html')

# 入手記録入力画面
def obtain_edit(request):
	return render(request, 'records/obtain_edit.html')

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
