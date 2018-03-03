from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack

from django.urls import path

from app.authentication import QueryAuthMiddleware

from .consumers import FrontendConsumer

application = ProtocolTypeRouter({
    'websocket': QueryAuthMiddleware(
        SessionMiddlewareStack(URLRouter([
            path('frontend/', FrontendConsumer),
        ]))),
})
