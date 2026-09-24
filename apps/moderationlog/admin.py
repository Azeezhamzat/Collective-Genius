from django.contrib import admin

from .models import LogEntry


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('project', 'flag', 'action', 'created')
    list_filter = ('flag', 'action', 'project')
    readonly_fields = ('project', 'flag', 'action', 'created')
