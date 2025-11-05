"""Google Pub/Sub prototype script for learning."""
import json
import logging
import os
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

# Initialize publisher client with credentials if we loaded them directly
if credentials:
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    logging.info(f"Using service account: {credentials.service_account_email}")
    # Get project_id from credentials if available
    with open(local_credentials_file) as f:
        creds_data = json.load(f)
        project_id = creds_data.get("project_id", "level-calculus-237812")
else:
    # It will automatically use GOOGLE_APPLICATION_CREDENTIALS if set
    publisher = pubsub_v1.PublisherClient()
    project_id = "level-calculus-237812"  # ProtoType Project ID
topic_id = "prototype-topic"
topic_path = publisher.topic_path(project_id, topic_id)

# Ensure topic exists (create if it doesn't)
# If we don't have permission to create, we'll try to publish anyway
try:
    publisher.create_topic(request={"name": topic_path})
    logging.info(f"Created Pub/Sub topic: {topic_path}")
except AlreadyExists:
    logging.info(f"Pub/Sub topic already exists: {topic_path}")
except PermissionDenied:
    logging.warning(
        f"Permission denied to create topic {topic_path}. "
        f"Attempting to publish anyway (topic may already exist)."
    )
except Exception as e:
    logging.warning(
        f"Could not create topic {topic_path}: {e}. "
        f"Attempting to publish anyway (topic may already exist)."
    )

# Publish a message
message_data = "Hello, World, Google Pub/Sub!"
logging.info(f"Publishing message to topic: {topic_id}")

try:
    future = publisher.publish(topic_path, message_data.encode("utf-8"))
    message_id = future.result()
    print(f"✓ Message published successfully! Message ID: {message_id}")
except NotFound as e:
    print("\n" + "=" * 60)
    print("ERROR: Topic not found!")
    print("=" * 60)
    print(f"\nThe topic '{topic_id}' does not exist in project '{project_id}'.")
    print("\nTo fix this, you have two options:")
    print("\n1. Create the topic manually in Google Cloud Console:")
    print(f"   - Go to: https://console.cloud.google.com/cloudpubsub/topic/list?project={project_id}")
    print(f"   - Click 'Create Topic'")
    print(f"   - Name it: {topic_id}")
    print("\n2. Grant your service account permission to create topics:")
    print("   - Go to: IAM & Admin → IAM")
    print("   - Find your service account and add 'Pub/Sub Admin' role")
    print("\n" + "=" * 60)
    raise
except PermissionDenied as e:
    print("\n" + "=" * 60)
    print("ERROR: Permission denied!")
    print("=" * 60)
    print(f"\nYour service account doesn't have permission to publish to topic '{topic_id}'.")
    print("\nTo fix this:")
    print("   - Go to: IAM & Admin → IAM")
    print("   - Find your service account and add 'Pub/Sub Publisher' role")
    print("\n" + "=" * 60)
    raise
except Exception as e:
    print(f"\nERROR: Failed to publish message: {e}")
    raise