from django.urls import path

from . import consumers


websocket_urlpatterns = [
    path("ws/<str:name>/credibility/<path:url>", consumers.Credibility.as_asgi()),
]
