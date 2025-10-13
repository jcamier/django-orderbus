import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from .serializers import OrderWebhookSerializer
from .publishers import publish_order_created

logger = logging.getLogger(__name__)


@api_view(["POST"])
def order_webhook(request):
    """
    Webhook endpoint to receive order creation events.

    Expected payload:
    {
        "order_id": "SO-10045",
        "customer": {"name": "Jane Doe", "email": "jane@example.com"},
        "items": [
            {"sku": "ABC123", "name": "Solar Panel", "quantity": 2, "unit_price": 150.0}
        ],
        "shipping_address": "123 Main St, Austin, TX 78701",
        "total": 350.0
    }

    Returns:
        201 Created: {"ok": true, "order_id": "SO-10045"}
        400 Bad Request: {"errors": {...}}
    """
    serializer = OrderWebhookSerializer(data=request.data)

    if not serializer.is_valid():
        logger.warning(f"Invalid order webhook payload: {serializer.errors}")
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Use atomic transaction to ensure order + items are saved together
        with transaction.atomic():
            order = serializer.save()
            logger.info(f"Order created: {order.external_ref}")

        # Publish event to Pub/Sub (outside transaction to avoid rollback issues)
        try:
            publish_order_created(order)
            logger.info(f"Published order.created event for: {order.external_ref}")
        except Exception as e:
            # Log but don't fail the request - order is already saved
            logger.error(f"Failed to publish order.created event: {e}", exc_info=True)

        return Response(
            {"ok": True, "order_id": order.external_ref}, status=status.HTTP_201_CREATED
        )

    except Exception as e:
        logger.error(f"Error processing order webhook: {e}", exc_info=True)
        return Response(
            {"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
