"""
ASGI config for orderbus project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orderbus.settings')

# Initialize OpenTelemetry before Django application
try:
    from orderbus.otel import setup_otel
    setup_otel()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to initialize OpenTelemetry: {e}")

application = get_asgi_application()
