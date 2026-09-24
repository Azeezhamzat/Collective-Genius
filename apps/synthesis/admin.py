from django.contrib import admin

from .models import StatementResult
from .models import SynthesisSnapshot


class StatementResultInline(admin.TabularInline):
    model = StatementResult
    extra = 0
    readonly_fields = ('comment', 'n_votes', 'agree_ratio',
                       'consensus_score', 'divisiveness')
    can_delete = False


@admin.register(SynthesisSnapshot)
class SynthesisSnapshotAdmin(admin.ModelAdmin):
    list_display = ('module', 'created', 'n_participants', 'n_statements',
                    'n_groups')
    list_filter = ('module',)
    readonly_fields = ('created',)
    inlines = [StatementResultInline]
