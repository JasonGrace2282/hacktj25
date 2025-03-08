from channels.generic.websocket import WebsocketConsumer

from .models import BiasedContent


class Credibility(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, **kwargs):
        pass

    def bias_from_text(self, text: str) -> BiasedContent:
        raise Exception("TODO")
