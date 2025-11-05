"""Google Pub/Sub subscriber script for learning."""
import json
import logging
import os
import sys
from pathlib import Path
from decouple import config
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.api_core.exceptions import AlreadyExists, NotFound, PermissionDenied

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Try to load credentials from local JSON file first, then fall back to .env
script_dir = Path(__file__).resolve().parent
local_credentials_file = script_dir / "google-service-account-key.json"

credentials = None

if local_credentials_file.exists():
    # Use the local JSON file directly
    logging.info(f"Using local credentials file: {local_credentials_file}")
    credentials = service_account.Credentials.from_service_account_file(
        str(local_credentials_file)
    )
    # Also set environment variable for consistency
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(local_credentials_file)
else:
    # Fall back to .env file
    logging.info("Local credentials file not found, checking .env file...")
    env_path = Path(__file__).resolve().parent.parent / ".env"
    credentials_path = config("GOOGLE_APPLICATION_CREDENTIALS", default=None)

    if credentials_path:
        # Expand ~ in path (e.g., ~/file.json -> /Users/username/file.json)
        credentials_path = os.path.expanduser(credentials_path)
        credentials_file = Path(credentials_path)

        if not credentials_file.exists():
            raise FileNotFoundError(
                f"Google credentials file not found: {credentials_path}\n"
                f"Please check your .env file and ensure the path is correct."
            )

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_file.resolve())
        logging.info(f"Using Google credentials from: {credentials_file.resolve()}")
    else:
        logging.warning(
            "GOOGLE_APPLICATION_CREDENTIALS not set in .env. "
            "Using default credentials if available."
        )

# Initialize subscriber client with credentials if we loaded them directly
if credentials:
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    logging.info(f"Using service account: {credentials.service_account_email}")
    # Get project_id from credentials if available
    with open(local_credentials_file) as f:
        creds_data = json.load(f)
        project_id = creds_data.get("project_id", "level-calculus-237812")
else:
    # It will automatically use GOOGLE_APPLICATION_CREDENTIALS if set
    subscriber = pubsub_v1.SubscriberClient()
    project_id = "level-calculus-237812"  # ProtoType Project ID

topic_id = "prototype-topic"
subscription_id = "prototype-subscription"
topic_path = subscriber.topic_path(project_id, topic_id)
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# Ensure subscription exists (create if it doesn't)
try:
    subscriber.create_subscription(
        request={"name": subscription_path, "topic": topic_path}
    )
    logging.info(f"Created Pub/Sub subscription: {subscription_path}")
except AlreadyExists:
    logging.info(f"Pub/Sub subscription already exists: {subscription_path}")
except PermissionDenied:
    logging.warning(
        f"Permission denied to create subscription {subscription_path}. "
        f"Attempting to pull messages anyway (subscription may already exist)."
    )
except NotFound:
    print("\n" + "=" * 60)
    print("ERROR: Topic not found!")
    print("=" * 60)
    print(f"\nThe topic '{topic_id}' does not exist in project '{project_id}'.")
    print("\nPlease create the topic first using publisher.py or in the Google Cloud Console.")
    print("\n" + "=" * 60)
    sys.exit(1)
except Exception as e:
    logging.warning(
        f"Could not create subscription {subscription_path}: {e}. "
        f"Attempting to pull messages anyway (subscription may already exist)."
    )


def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    """Callback function to handle received messages."""
    print("\n" + "=" * 60)
    print("📨 Message Received!")
    print("=" * 60)
    print(f"Message ID: {message.message_id}")
    print(f"Publish Time: {message.publish_time}")

    # Try to decode as UTF-8 text
    try:
        message_data = message.data.decode("utf-8")
        print(f"\nMessage Data:")
        print(f"  {message_data}")

        # Try to parse as JSON if possible
        try:
            json_data = json.loads(message_data)
            print(f"\nMessage Data (JSON):")
            print(json.dumps(json_data, indent=2))
        except json.JSONDecodeError:
            pass  # Not JSON, that's fine
    except Exception as e:
        print(f"\nMessage Data (raw bytes, couldn't decode):")
        print(f"  {message.data}")

    # Print attributes if any
    if message.attributes:
        print(f"\nAttributes:")
        for key, value in message.attributes.items():
            print(f"  {key}: {value}")

    print("=" * 60)

    # Acknowledge the message so it's not redelivered
    message.ack()
    print("✓ Message acknowledged\n")


# Pull messages
print("\n" + "=" * 60)
print("🔔 Listening for messages...")
print("=" * 60)
print(f"Topic: {topic_id}")
print(f"Subscription: {subscription_id}")
print(f"Project: {project_id}")
print("\nPress Ctrl+C to stop\n")

try:
    # Pull messages synchronously (one at a time)
    # This will block and wait for messages
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    # Keep the main thread alive
    streaming_pull_future.result()
except KeyboardInterrupt:
    print("\n\nStopping subscriber...")
    streaming_pull_future.cancel()
    print("✓ Subscriber stopped")
except Exception as e:
    print(f"\nERROR: Failed to subscribe: {e}")
    sys.exit(1)


