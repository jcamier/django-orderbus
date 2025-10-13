"""
Google Pub/Sub publisher for order events.
"""
import json
import logging
from google.cloud import pubsub_v1
from django.conf import settings
from .pubsub_utils import get_topic_path, ensure_topic_exists

logger = logging.getLogger(__name__)


def publish_order_created(order):
    """
    Publish an order.created event to Google Pub/Sub.

    Args:
        order: Order instance to publish

    Raises:
        Exception: If publishing fails
    """
    # Prepare event payload
    event_data = {
        "event": "order.created",
        "order_id": order.external_ref,
        "customer_name": order.customer_name,
        "total": str(order.total),
        "created_at": order.created_at.isoformat(),
    }

    logger.info(f"Publishing order.created event for: {order.external_ref}")

    try:
        # Ensure topic exists (idempotent)
        topic_path = ensure_topic_exists()

        # Create publisher client
        publisher = pubsub_v1.PublisherClient()

        # Convert event data to JSON bytes
        message_data = json.dumps(event_data).encode("utf-8")

        # Publish message
        future = publisher.publish(topic_path, message_data)

        # Wait for publish confirmation (with timeout)
        message_id = future.result(timeout=2.0)

        logger.info(
            f"Published order.created event to Pub/Sub. Message ID: {message_id}, Order: {order.external_ref}"
        )

        return message_id

    except Exception as e:
        logger.error(f"Failed to publish order.created event for {order.external_ref}: {e}")
        raise

