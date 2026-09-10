from django.contrib import admin
from .models import Script, ScriptExecution, AdminFile


@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at', 'updated_at']
    list_filter = ['user', 'created_at']
    search_fields = ['name', 'description', 'code']


@admin.register(ScriptExecution)
class ScriptExecutionAdmin(admin.ModelAdmin):
    list_display = ['script', 'user', 'status', 'executed_at']
    list_filter = ['status', 'user', 'executed_at']
    search_fields = ['script__name', 'user__username']
    readonly_fields = ['logs', 'executed_at']


@admin.register(AdminFile)
class AdminFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'uploaded_by', 'file_size', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_by', 'uploaded_at']
    search_fields = ['name', 'description']
    readonly_fields = ['file_size', 'uploaded_at', 'updated_at']

