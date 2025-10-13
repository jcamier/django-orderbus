"""
Google Pub/Sub publisher for order events.
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def publish_order_created(order):
    """
    Publish an order.created event to Google Pub/Sub.

    Args:
        order: Order instance to publish

    Raises:
        Exception: If publishing fails
    """
    # TODO: Implement actual Pub/Sub publishing
    # For now, just log the event
    event_data = {
        "event": "order.created",
        "order_id": order.external_ref,
        "customer_name": order.customer_name,
        "total": str(order.total),
        "created_at": order.created_at.isoformat(),
    }

    logger.info(f"[PLACEHOLDER] Would publish to Pub/Sub: {json.dumps(event_data)}")

    # We'll implement the actual Pub/Sub publishing next
    pass

