from django.db import models


class Order(models.Model):
    """
    Represents an order received from an external system (e.g., Shopify).
    """

    external_ref = models.CharField(
        max_length=255, unique=True, db_index=True, help_text="Unique order ID from external system"
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        help_text="Idempotency key to prevent duplicate processing",
    )
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    shipping_address = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order {self.external_ref} - {self.customer_name}"


class OrderItem(models.Model):
    """
    Represents an item within an order.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    sku = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.name} (SKU: {self.sku})"

    @property
    def line_total(self):
        """Calculate total price for this line item."""
        if self.quantity is not None and self.unit_price is not None:
            return self.quantity * self.unit_price
        return None
