from django.contrib import admin

from .models import Proposal
from .models import Response


class ResponseInline(admin.TabularInline):
    model = Response
    extra = 0
    readonly_fields = ('creator', 'stance', 'reason', 'resolved',
                       'modified')
    can_delete = False


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'creator', 'created')
    list_filter = ('module',)
    inlines = [ResponseInline]
