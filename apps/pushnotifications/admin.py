from django.contrib import admin

from .models import PhaseReminderSent
from .models import PushDelivery
from .models import PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created')
    list_filter = ('project',)
    readonly_fields = ('endpoint', 'p256dh_key', 'auth_key', 'created')


@admin.register(PushDelivery)
class PushDeliveryAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'subscription', 'status',
                    'attempt_number', 'created')
    list_filter = ('status', 'event_type')
    readonly_fields = ('subscription', 'event_type', 'payload',
                       'attempt_number', 'status', 'error',
                       'next_retry_at', 'created', 'modified')


@admin.register(PhaseReminderSent)
class PhaseReminderSentAdmin(admin.ModelAdmin):
    list_display = ('phase', 'sent_at')
    readonly_fields = ('phase', 'sent_at')
