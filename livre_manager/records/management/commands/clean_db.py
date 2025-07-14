"""
records/management/commands/full_clean_records.py

データベースのレコードを整形・フォーマットするためのスクリプト。
各テーブルのレコードに対して clean() が適用される。

使用方法:
python3 manage.py clean_db
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from records.models import Acquisition, AcquiredItem, Book  # 適用したいモデルをインポート

class Command(BaseCommand):
	help = 'Applies the clean() method to all existing records of YourModel.'
	
	def handle(self, *args, **options):
		self.stdout.write(self.style.SUCCESS('Starting to apply clean() to existing records...'))
		
		self.clean(Acquisition)
		self.clean(AcquiredItem)
		self.clean(Book)
	
	def clean(self, model, batch_size=1000):
		self.stdout.write(self.style.SUCCESS(f'Applying clean() to {model.__name__} records...'))
		
		queryset = model.objects.all()
		
		updated_count = 0
		error_count = 0
		
		for i in range(0, queryset.count(), batch_size):
			batch = queryset[i:i + batch_size]
			for record in batch:
				try:
					record.full_clean()
					record.save()
					updated_count += 1
				except Exception as e:
					self.stderr.write(self.style.ERROR(f'Error applying clean() to record ID {record.pk}: {e}'))
					error_count += 1
			self.stdout.write(f'Processed {i + len(batch)} records...')
		
		self.stdout.write(self.style.SUCCESS(f'Finished. Successfully processed {updated_count} records. Failed on {error_count} records.'))
