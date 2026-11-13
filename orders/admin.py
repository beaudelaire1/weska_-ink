from django.contrib import admin
from .models import Customer, DeliveryZone, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "sku", "quantity", "unit_price_cents", "unit_cost_cents")


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ("old_status", "new_status", "note", "actor", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "created_at", "customer", "channel", "status", "total_cents", "fulfillment")
    list_filter = ("channel", "status", "fulfillment", "created_at")
    search_fields = ("number", "customer__full_name", "customer__email")
    readonly_fields = (
        "number", "customer", "channel", "status", "fulfillment", "delivery_zone", "delivery_zone_name",
        "shipping_address", "shipping_postal_code", "shipping_city", "subtotal_cents", "shipping_cents",
        "discount_cents", "total_cents", "payment_method", "created_by", "created_at", "updated_at",
    )
    inlines = (OrderItemInline, OrderStatusHistoryInline)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "communes", "fee_cents", "is_active")
    list_editable = ("fee_cents", "is_active")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "created_at")
    search_fields = ("full_name", "email", "phone")
