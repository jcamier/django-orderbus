"""
Google Pub/Sub utilities for topic and subscription management.
"""
import logging
from google.cloud import pubsub_v1
from google.api_core.exceptions import AlreadyExists
from django.conf import settings

logger = logging.getLogger(__name__)


def get_topic_path():
    """Get the full topic path."""
    publisher = pubsub_v1.PublisherClient()
    return publisher.topic_path(settings.PUBSUB_PROJECT_ID, settings.PUBSUB_TOPIC_ORDER_CREATED)


def get_subscription_path():
    """Get the full subscription path."""
    subscriber = pubsub_v1.SubscriberClient()
    return subscriber.subscription_path(
        settings.PUBSUB_PROJECT_ID, settings.PUBSUB_SUBSCRIPTION_ORDER_CREATED
    )


def ensure_topic_exists():
    """
    Ensure the Pub/Sub topic exists, create if it doesn't.

    Returns:
        str: Topic path
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = get_topic_path()

    try:
        publisher.create_topic(request={"name": topic_path})
        logger.info(f"Created Pub/Sub topic: {topic_path}")
    except AlreadyExists:
        logger.debug(f"Pub/Sub topic already exists: {topic_path}")
    except Exception as e:
        logger.error(f"Error creating topic {topic_path}: {e}")
        raise

    return topic_path


def ensure_subscription_exists():
    """
    Ensure the Pub/Sub subscription exists, create if it doesn't.

    Returns:
        str: Subscription path
    """
    subscriber = pubsub_v1.SubscriberClient()
    topic_path = get_topic_path()
    subscription_path = get_subscription_path()

    try:
        subscriber.create_subscription(request={"name": subscription_path, "topic": topic_path})
        logger.info(f"Created Pub/Sub subscription: {subscription_path}")
    except AlreadyExists:
        logger.debug(f"Pub/Sub subscription already exists: {subscription_path}")
    except Exception as e:
        logger.error(f"Error creating subscription {subscription_path}: {e}")
        raise

    return subscription_path


def setup_pubsub():
    """
    Setup Pub/Sub topic and subscription.
    Idempotent - safe to call multiple times.
    """
    ensure_topic_exists()
    ensure_subscription_exists()
    logger.info("Pub/Sub setup complete")

