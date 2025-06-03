from django.contrib import admin

from .models import ObtainRecord, ObtainedItem

# Register your models here.

@admin.register(ObtainRecord)
class ObtainRecordAdmin(admin.ModelAdmin):
	def get_readonly_fields(self, request, obj=None):
		# 常にreadonlyにしたいフィールド
		readonly_base_fields = ['created_at', 'updated_at']
		
		# モデルで定義したカスタム属性からreadonly_fieldsを取得する場合
		if hasattr(self.model, 'ADMIN_READONLY_FIELDS'):
			readonly_base_fields.extend(list(self.model.ADMIN_READONLY_FIELDS))
		
		# # 例: 特定の条件でreadonlyにするフィールドを追加
		# if obj and not obj.is_active:  # オブジェクトが非アクティブなら 'some_editable_field' もreadonlyに
		# 	readonly_base_fields.append('some_editable_field')
		
		# 重複を排除して返す（setに変換してlistに戻す）
		return list(set(readonly_base_fields))

@admin.register(ObtainedItem)
class ObtainedItemAdmin(admin.ModelAdmin):
	def get_readonly_fields(self, request, obj=None):
		# 常にreadonlyにしたいフィールド
		readonly_base_fields = ['created_at', 'updated_at']
		
		# モデルで定義したカスタム属性からreadonly_fieldsを取得する場合
		if hasattr(self.model, 'ADMIN_READONLY_FIELDS'):
			readonly_base_fields.extend(list(self.model.ADMIN_READONLY_FIELDS))
		
		# # 例: 特定の条件でreadonlyにするフィールドを追加
		# if obj and not obj.is_active:  # オブジェクトが非アクティブなら 'some_editable_field' もreadonlyに
		# 	readonly_base_fields.append('some_editable_field')
		
		# 重複を排除して返す（setに変換してlistに戻す）
		return list(set(readonly_base_fields))
