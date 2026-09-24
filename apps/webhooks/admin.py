from django.contrib import admin

from .models import Delivery
from .models import Endpoint


class DeliveryInline(admin.TabularInline):
    model = Delivery
    extra = 0
    readonly_fields = ('event_type', 'status', 'response_status',
                       'attempt_number', 'next_retry_at', 'created')
    can_delete = False


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = ('url', 'organisation', 'is_active', 'created')
    list_filter = ('organisation', 'is_active')
    readonly_fields = ('secret', 'created')
    inlines = [DeliveryInline]


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'endpoint', 'status', 'attempt_number',
                    'created')
    list_filter = ('status', 'event_type')
    readonly_fields = ('endpoint', 'event_type', 'data', 'attempt_number',
                       'status', 'response_status', 'error',
                       'next_retry_at', 'created', 'modified')
