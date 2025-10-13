from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.Serializer):
    """
    Serializer for incoming webhook order items.
    Does not use ModelSerializer to match exact webhook payload structure.
    """

    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderWebhookSerializer(serializers.Serializer):
    """
    Serializer for incoming order webhook payload.
    Handles nested customer data and items.
    """

    order_id = serializers.CharField(max_length=255, source="external_ref")
    idempotency_key = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )
    customer = serializers.DictField()
    items = OrderItemSerializer(many=True)
    shipping_address = serializers.CharField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_customer(self, value):
        """Validate customer dictionary has required fields."""
        if "name" not in value:
            raise serializers.ValidationError("Customer name is required")
        if "email" not in value:
            raise serializers.ValidationError("Customer email is required")
        return value

    def validate_items(self, value):
        """Validate that at least one item exists."""
        if not value:
            raise serializers.ValidationError("At least one item is required")
        return value

    def create(self, validated_data):
        """
        Create Order and related OrderItems from validated webhook data.
        Handles idempotency - if order with same idempotency_key exists, returns existing order.
        """
        # Extract nested data
        customer_data = validated_data.pop("customer")
        items_data = validated_data.pop("items")
        idempotency_key = validated_data.get("idempotency_key")

        # Check for existing order with same idempotency key
        if idempotency_key:
            existing_order = Order.objects.filter(idempotency_key=idempotency_key).first()
            if existing_order:
                # Return existing order without creating duplicate
                return existing_order

        # Create Order
        order = Order.objects.create(
            external_ref=validated_data["external_ref"],
            idempotency_key=idempotency_key,
            customer_name=customer_data["name"],
            customer_email=customer_data["email"],
            shipping_address=validated_data["shipping_address"],
            total=validated_data["total"],
        )

        # Create OrderItems
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model with nested items (for reading).
    """

    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "external_ref",
            "customer_name",
            "customer_email",
            "shipping_address",
            "total",
            "created_at",
            "items",
        ]

    def get_items(self, obj):
        """Return order items as a list of dictionaries."""
        return [
            {
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "line_total": str(item.line_total),
            }
            for item in obj.items.all()
        ]

