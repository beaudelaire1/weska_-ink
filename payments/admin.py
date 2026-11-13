from django.contrib import admin
from .models import Payment, PaymentEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "external_id", "amount_cents", "status", "created_at")
    list_filter = ("provider", "status", "created_at")
    search_fields = ("order__number", "external_id")
    readonly_fields = ("order", "provider", "external_id", "amount_cents", "currency", "status", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ("provider_event_id", "event_type", "received_at", "processed_at", "processing_error")
    readonly_fields = tuple(field.name for field in PaymentEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
