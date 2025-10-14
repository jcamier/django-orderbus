"""
Webhook security utilities including HMAC signature verification.
"""
import hmac
import hashlib
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_webhook_signature(request_body, signature_header, secret=None):
    """
    Verify HMAC-SHA256 signature for incoming webhooks.

    Args:
        request_body: Raw request body (bytes)
        signature_header: Signature from request header (e.g., X-Shopify-Hmac-SHA256)
        secret: Webhook secret key (defaults to settings.WEBHOOK_SECRET)

    Returns:
        bool: True if signature is valid, False otherwise

    Example Shopify header:
        X-Shopify-Hmac-SHA256: base64_encoded_signature
    """
    if secret is None:
        secret = getattr(settings, "WEBHOOK_SECRET", None)

    if not secret:
        logger.warning("WEBHOOK_SECRET not configured - skipping signature verification")
        return True  # Allow in development if not configured

    if not signature_header:
        logger.warning("No signature header provided")
        return False

    try:
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode("utf-8"), request_body, hashlib.sha256
        ).hexdigest()

        # Compare signatures (constant-time comparison to prevent timing attacks)
        is_valid = hmac.compare_digest(expected_signature, signature_header)

        if not is_valid:
            logger.warning(
                f"Invalid webhook signature. Expected: {expected_signature[:10]}..., "
                f"Got: {signature_header[:10]}..."
            )

        return is_valid

    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}", exc_info=True)
        return False


def verify_shopify_webhook(request_body, signature_header, secret=None):
    """
    Verify Shopify webhook signature (base64-encoded HMAC-SHA256).

    Shopify sends: X-Shopify-Hmac-SHA256: <base64_signature>

    Args:
        request_body: Raw request body (bytes)
        signature_header: Base64-encoded signature from X-Shopify-Hmac-SHA256 header
        secret: Shopify webhook secret

    Returns:
        bool: True if signature is valid
    """
    import base64

    if not signature_header:
        return False

    if secret is None:
        secret = getattr(settings, "WEBHOOK_SECRET", None)

    if not secret:
        logger.warning("WEBHOOK_SECRET not configured")
        return True

    try:
        # Calculate expected signature
        expected_hmac = base64.b64encode(
            hmac.new(secret.encode("utf-8"), request_body, hashlib.sha256).digest()
        ).decode()

        # Compare signatures
        is_valid = hmac.compare_digest(expected_hmac, signature_header)

        if not is_valid:
            logger.warning("Invalid Shopify webhook signature")

        return is_valid

    except Exception as e:
        logger.error(f"Error verifying Shopify webhook: {e}", exc_info=True)
        return False


def generate_webhook_signature(payload, secret):
    """
    Generate HMAC-SHA256 signature for outgoing webhooks.

    Args:
        payload: String or bytes payload
        secret: Secret key

    Returns:
        str: Hex-encoded signature
    """
    if isinstance(payload, str):
        payload = payload.encode("utf-8")

    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    return signature

