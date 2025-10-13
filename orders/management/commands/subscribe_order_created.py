"""
Django management command to subscribe to order.created Pub/Sub events.
"""
import json
import logging
import signal
import sys
from django.core.management.base import BaseCommand
from google.cloud import pubsub_v1
from orders.pubsub_utils import get_subscription_path, setup_pubsub
from orders.webhooks import send_order_created_webhook

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Subscribe to order.created Pub/Sub events and send egress webhooks"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriber = None
        self.streaming_pull_future = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-messages",
            type=int,
            default=None,
            help="Maximum number of messages to process before exiting (default: run indefinitely)",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        max_messages = options.get("max_messages")

        self.stdout.write(self.style.SUCCESS("Starting Pub/Sub subscriber for order.created events"))

        # Setup topic and subscription if they don't exist
        try:
            setup_pubsub()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to setup Pub/Sub: {e}"))
            sys.exit(1)

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Start subscriber
        self._start_subscriber(max_messages)

    def _start_subscriber(self, max_messages=None):
        """Start the Pub/Sub subscriber."""
        subscription_path = get_subscription_path()
        self.subscriber = pubsub_v1.SubscriberClient()

        message_count = 0

        def callback(message):
            """Process incoming Pub/Sub message."""
            nonlocal message_count

            try:
                # Parse message data
                event_data = json.loads(message.data.decode("utf-8"))
                order_id = event_data.get("order_id", "unknown")

                self.stdout.write(
                    self.style.SUCCESS(f"Received order.created event for: {order_id}")
                )
                logger.info(f"Processing Pub/Sub message: {event_data}")

                # Send egress webhook
                success = send_order_created_webhook(event_data)

                if success:
                    # Acknowledge message on success
                    message.ack()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Sent egress webhook for order: {order_id}")
                    )
                    message_count += 1
                else:
                    # Nack message on failure (will be redelivered)
                    message.nack()
                    self.stdout.write(
                        self.style.WARNING(f"✗ Failed to send webhook for order: {order_id} (will retry)")
                    )

                # Check if we've hit max messages
                if max_messages and message_count >= max_messages:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Processed {message_count} messages. Shutting down..."
                        )
                    )
                    self._shutdown()

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in Pub/Sub message: {e}")
                message.ack()  # Ack to prevent infinite retries
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                message.nack()

        try:
            # Start streaming pull
            self.streaming_pull_future = self.subscriber.subscribe(
                subscription_path, callback=callback
            )

            self.stdout.write(
                self.style.SUCCESS(f"Listening for messages on {subscription_path}...")
            )
            self.stdout.write(self.style.WARNING("Press Ctrl+C to stop"))

            # Block until shutdown
            self.streaming_pull_future.result()

        except Exception as e:
            logger.error(f"Subscriber error: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"Subscriber error: {e}"))
            self._shutdown()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.stdout.write(self.style.WARNING("\nReceived shutdown signal. Cleaning up..."))
        self._shutdown()

    def _shutdown(self):
        """Shutdown the subscriber gracefully."""
        if self.streaming_pull_future:
            self.streaming_pull_future.cancel()
            self.stdout.write(self.style.SUCCESS("Subscriber stopped"))
        sys.exit(0)

