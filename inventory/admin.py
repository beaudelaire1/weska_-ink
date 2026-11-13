from django.contrib import admin
from .models import StockItem, StockMovement, StockReservation


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity_on_hand", "quantity_reserved", "available", "alert_threshold", "updated_at")
    list_filter = ("product__collection",)
    search_fields = ("product__name", "product__sku")
    readonly_fields = ("product", "quantity_on_hand", "quantity_reserved", "alert_threshold", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "stock_item", "movement_type", "quantity_delta", "reason", "actor")
    list_filter = ("movement_type", "created_at")
    search_fields = ("stock_item__product__name", "reason", "order__number")
    readonly_fields = ("created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "status", "expires_at")
    list_filter = ("status",)
    readonly_fields = tuple(field.name for field in StockReservation._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
