from django.contrib import admin

from .models import KeyComment
from .models import SummarySnapshot


class KeyCommentInline(admin.TabularInline):
    model = KeyComment
    extra = 0
    readonly_fields = ('comment', 'score', 'rank')
    can_delete = False


@admin.register(SummarySnapshot)
class SummarySnapshotAdmin(admin.ModelAdmin):
    list_display = ('module', 'created', 'n_comments')
    list_filter = ('module',)
    readonly_fields = ('created',)
    inlines = [KeyCommentInline]
