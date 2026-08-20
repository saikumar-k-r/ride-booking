from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path(
        "ws/rides/<uuid:ride_id>/",
        consumers.RideConsumer.as_asgi(),
    ),
]