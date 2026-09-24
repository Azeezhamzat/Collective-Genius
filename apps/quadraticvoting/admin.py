from django.contrib import admin

from .models import Option
from .models import VotingRound


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


@admin.register(VotingRound)
class VotingRoundAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'credit_budget', 'is_open',
                    'created')
    list_filter = ('module', 'is_open')
    inlines = [OptionInline]
