"""
WSGI config for orderbus project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orderbus.settings')

# Initialize OpenTelemetry before Django application
try:
    from orderbus.otel import setup_otel
    setup_otel()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to initialize OpenTelemetry: {e}")

application = get_wsgi_application()
