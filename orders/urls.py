from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("webhooks/orders/create/", views.order_webhook, name="order_webhook"),
]

