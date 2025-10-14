#!/usr/bin/env python
"""
Test script for webhook HMAC signature verification.
Demonstrates how to send properly signed webhooks.
"""
import json
import hmac
import hashlib
import base64
import requests

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhooks/orders/create/"
WEBHOOK_SECRET = "your-secret-key-here"  # Match your .env WEBHOOK_SECRET


def generate_hmac_signature(payload_str, secret):
    """Generate HMAC-SHA256 signature (hex format)."""
    return hmac.new(
        secret.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def generate_shopify_signature(payload_str, secret):
    """Generate Shopify-style HMAC-SHA256 signature (base64 format)."""
    return base64.b64encode(
        hmac.new(secret.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).digest()
    ).decode()


def test_webhook_with_signature():
    """Test webhook with valid HMAC signature."""
    payload = {
        "order_id": "SO-99999",
        "idempotency_key": "hmac-test-001",
        "customer": {"name": "HMAC Test User", "email": "hmac@example.com"},
        "items": [{"sku": "SECURE-001", "name": "Secure Product", "quantity": 1, "unit_price": 999.99}],
        "shipping_address": "999 Secure St, Auth City, CA 90210",
        "total": 999.99,
    }

    # Convert to JSON string
    payload_str = json.dumps(payload)

    # Generate signature
    signature = generate_hmac_signature(payload_str, WEBHOOK_SECRET)

    # Send request with signature header
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }

    print("=" * 60)
    print("TEST 1: Valid HMAC Signature")
    print("=" * 60)
    print(f"Payload: {payload_str}")
    print(f"Signature: {signature}")
    print(f"Headers: {headers}")

    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    print("\n✅ Expected: 201 Created\n")


def test_webhook_invalid_signature():
    """Test webhook with invalid HMAC signature."""
    payload = {
        "order_id": "SO-99998",
        "idempotency_key": "hmac-test-002",
        "customer": {"name": "Invalid Signature Test", "email": "invalid@example.com"},
        "items": [{"sku": "INSECURE-001", "name": "Hacker Product", "quantity": 1, "unit_price": 1.00}],
        "shipping_address": "123 Hacker Lane",
        "total": 1.00,
    }

    # Send request with WRONG signature
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": "wrong_signature_12345",
    }

    print("=" * 60)
    print("TEST 2: Invalid HMAC Signature (Should Fail)")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload)}")
    print(f"Headers: {headers}")

    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    print("\n❌ Expected: 401 Unauthorized\n")


def test_webhook_no_signature():
    """Test webhook without signature header (should fail if WEBHOOK_SECRET is set)."""
    payload = {
        "order_id": "SO-99997",
        "idempotency_key": "hmac-test-003",
        "customer": {"name": "No Signature Test", "email": "nosig@example.com"},
        "items": [{"sku": "NOSIG-001", "name": "No Sig Product", "quantity": 1, "unit_price": 1.00}],
        "shipping_address": "456 No Auth St",
        "total": 1.00,
    }

    headers = {
        "Content-Type": "application/json",
        # No signature header
    }

    print("=" * 60)
    print("TEST 3: No Signature Header (Should Fail)")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload)}")
    print(f"Headers: {headers}")

    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    print("\n❌ Expected: 401 Unauthorized\n")


def test_shopify_webhook():
    """Test Shopify-style webhook with base64 signature."""
    payload = {
        "order_id": "SO-99996",
        "idempotency_key": "shopify-test-001",
        "customer": {"name": "Shopify Test", "email": "shopify@example.com"},
        "items": [{"sku": "SHOP-001", "name": "Shopify Product", "quantity": 2, "unit_price": 49.99}],
        "shipping_address": "789 Shopify Ave, E-commerce City",
        "total": 99.98,
    }

    payload_str = json.dumps(payload)

    # Generate Shopify-style signature (base64)
    signature = generate_shopify_signature(payload_str, WEBHOOK_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Hmac-SHA256": signature,
    }

    print("=" * 60)
    print("TEST 4: Shopify-Style HMAC Signature (Base64)")
    print("=" * 60)
    print(f"Payload: {payload_str}")
    print(f"Shopify Signature: {signature}")
    print(f"Headers: {headers}")

    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    print("\n✅ Expected: 201 Created\n")


if __name__ == "__main__":
    print("\n🔐 Webhook HMAC Signature Verification Tests\n")
    print(f"Testing against: {WEBHOOK_URL}")
    print(f"Using secret: {WEBHOOK_SECRET[:10]}...\n")

    try:
        # Test with valid signature
        test_webhook_with_signature()

        # Test with invalid signature
        test_webhook_invalid_signature()

        # Test without signature
        test_webhook_no_signature()

        # Test Shopify format
        test_shopify_webhook()

        print("=" * 60)
        print("✅ All tests complete!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Django server")
        print("Make sure Django is running: python manage.py runserver\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

