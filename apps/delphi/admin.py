from django.contrib import admin

from .models import Question
from .models import Response


class ResponseInline(admin.TabularInline):
    model = Response
    extra = 0
    readonly_fields = ('creator', 'round_number', 'value', 'rationale',
                       'created')
    can_delete = False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'current_round', 'is_closed')
    list_filter = ('module', 'is_closed')
    inlines = [ResponseInline]
