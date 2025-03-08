from channels.generic.websocket import WebsocketConsumer



class Credibility(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, **kwargs):
        pass
