from django.contrib import admin

from .models import Stance


@admin.register(Stance)
class StanceAdmin(admin.ModelAdmin):
    list_display = ('comment', 'value', 'modified')
    list_filter = ('value',)
