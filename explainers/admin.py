"""
Admin configuration for explainers app.
"""
from django.contrib import admin
from .models import CodeExplanation


@admin.register(CodeExplanation)
class CodeExplanationAdmin(admin.ModelAdmin):
    list_display = ['language', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['code', 'explanation']

