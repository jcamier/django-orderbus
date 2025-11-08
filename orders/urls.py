from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path(
        "webhooks/orders/create/",
        views.OrderWebhookViewSet.as_view({"post": "create"}),
        name="order_webhook",
    ),
]

