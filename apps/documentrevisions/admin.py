from django.contrib import admin

from .models import ParagraphRevision


@admin.register(ParagraphRevision)
class ParagraphRevisionAdmin(admin.ModelAdmin):
    list_display = ('paragraph', 'created')
    list_filter = ('paragraph__chapter__module',)
    readonly_fields = ('paragraph', 'text', 'created')
