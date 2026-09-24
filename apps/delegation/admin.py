from django.contrib import admin

from .models import Delegation
from .models import DelegationRound
from .models import Option
from .models import Vote


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0


@admin.register(DelegationRound)
class DelegationRoundAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'is_open', 'created')
    list_filter = ('is_open',)
    inlines = [OptionInline]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('creator', 'option', 'delegation_round', 'modified')
    list_filter = ('delegation_round',)
    readonly_fields = ('creator', 'option', 'delegation_round', 'modified')


@admin.register(Delegation)
class DelegationAdmin(admin.ModelAdmin):
    list_display = ('delegator', 'delegatee', 'delegation_round', 'created')
    list_filter = ('delegation_round',)
    readonly_fields = ('delegator', 'delegatee', 'delegation_round',
                       'created')
