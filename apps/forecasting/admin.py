from django.contrib import admin

from .models import Forecast
from .models import Question


class ForecastInline(admin.TabularInline):
    model = Forecast
    extra = 0
    readonly_fields = ('creator', 'probability', 'modified')
    can_delete = False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'is_resolved', 'outcome',
                    'closes_at')
    list_filter = ('module', 'is_resolved')
    inlines = [ForecastInline]
