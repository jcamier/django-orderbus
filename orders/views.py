import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction, IntegrityError

from .models import Order
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
        "idempotency_key": "unique-key-12345",  # Optional but recommended
        "customer": {"name": "Jane Doe", "email": "jane@example.com"},
        "items": [
            {"sku": "ABC123", "name": "Solar Panel", "quantity": 2, "unit_price": 150.0}
        ],
        "shipping_address": "123 Main St, Austin, TX 78701",
        "total": 350.0
    }

    Idempotency:
        - If idempotency_key is provided and matches existing order, returns 200 (not 201)
        - If idempotency_key is not provided, uses order_id for duplicate detection

    Returns:
        201 Created: {"ok": true, "order_id": "SO-10045", "created": true}
        200 OK: {"ok": true, "order_id": "SO-10045", "created": false}  # Duplicate request
        400 Bad Request: {"errors": {...}}
    """
    serializer = OrderWebhookSerializer(data=request.data)

    if not serializer.is_valid():
        logger.warning(f"Invalid order webhook payload: {serializer.errors}")
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    idempotency_key = request.data.get("idempotency_key")
    is_new_order = False

    try:
        # Check if this is a duplicate request (idempotency check)
        if idempotency_key:
            existing_order = Order.objects.filter(idempotency_key=idempotency_key).first()
            if existing_order:
                logger.info(
                    f"Duplicate request detected via idempotency_key: {idempotency_key}, "
                    f"returning existing order: {existing_order.external_ref}"
                )
                return Response(
                    {
                        "ok": True,
                        "order_id": existing_order.external_ref,
                        "created": False,
                        "message": "Order already exists (idempotent request)",
                    },
                    status=status.HTTP_200_OK,
                )

        # Use atomic transaction to ensure order + items are saved together
        try:
            with transaction.atomic():
                order = serializer.save()
                is_new_order = True
                logger.info(f"Order created: {order.external_ref}")

        except IntegrityError as e:
            # Handle duplicate order_id (external_ref) gracefully
            order_id = request.data.get("order_id")
            logger.warning(
                f"Duplicate order_id detected: {order_id}. Returning existing order."
            )

            # Try to fetch the existing order
            existing_order = Order.objects.filter(external_ref=order_id).first()

            if existing_order:
                return Response(
                    {
                        "ok": True,
                        "order_id": existing_order.external_ref,
                        "created": False,
                        "message": "Order with this order_id already exists",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # Edge case: IntegrityError but can't find order (shouldn't happen)
                logger.error(f"IntegrityError but order not found: {order_id}")
                return Response(
                    {"error": "Duplicate order detected", "order_id": order_id},
                    status=status.HTTP_409_CONFLICT,
                )

        # Publish event to Pub/Sub only for new orders (outside transaction)
        if is_new_order:
            try:
                publish_order_created(order)
                logger.info(f"Published order.created event for: {order.external_ref}")
            except Exception as e:
                # Log but don't fail the request - order is already saved
                logger.error(f"Failed to publish order.created event: {e}", exc_info=True)

        return Response(
            {"ok": True, "order_id": order.external_ref, "created": is_new_order},
            status=status.HTTP_201_CREATED if is_new_order else status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error processing order webhook: {e}", exc_info=True)
        return Response(
            {"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
