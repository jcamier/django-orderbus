from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItems within Order admin."""

    model = OrderItem
    extra = 0
    fields = ("sku", "name", "quantity", "unit_price", "line_total")
    readonly_fields = ("line_total",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""

    list_display = (
        "external_ref",
        "customer_name",
        "customer_email",
        "total",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("external_ref", "customer_name", "customer_email")
    readonly_fields = ("created_at",)
    inlines = [OrderItemInline]

    fieldsets = (
        (
            "Order Information",
            {
                "fields": ("external_ref", "total", "created_at"),
            },
        ),
        (
            "Customer Information",
            {
                "fields": ("customer_name", "customer_email", "shipping_address"),
            },
        ),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model."""

    list_display = ("order", "sku", "name", "quantity", "unit_price", "line_total")
    list_filter = ("order__created_at",)
    search_fields = ("sku", "name", "order__external_ref")
    readonly_fields = ("line_total",)
