"""
Egress webhook handler for sending events to external systems.
"""
import json
import logging
from datetime import datetime
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def send_order_created_webhook(event_data):
    """
    Send order.created event to external webhook URL (e.g., RequestCatcher).

    Args:
        event_data: Dictionary containing event data

    Returns:
        bool: True if successful, False otherwise
    """
    webhook_url = settings.WEBHOOK_OUTGOING_URL

    # Prepare payload with timestamp
    payload = {
        "event": event_data.get("event"),
        "order_id": event_data.get("order_id"),
        "customer_name": event_data.get("customer_name"),
        "total": event_data.get("total"),
        "sent_at": datetime.utcnow().isoformat() + "Z",
    }

    try:
        logger.info(f"Sending egress webhook to {webhook_url} for order: {payload['order_id']}")

        # Send POST request with timeout
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

        response.raise_for_status()

        logger.info(
            f"Egress webhook sent successfully. Status: {response.status_code}, Order: {payload['order_id']}"
        )

        return True

    except httpx.HTTPError as e:
        logger.error(f"HTTP error sending egress webhook: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending egress webhook: {e}")
        return False

