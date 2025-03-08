from collections.abc import Iterator
from channels.generic.websocket import WebsocketConsumer

from .models import BiasedContent, BiasedMedia


class Credibility(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, **kwargs):
        pass


    def find_biased_content(self, name: str, url: str) -> Iterator[BiasedContent]:
        media = BiasedMedia.objects.filter(url=url).first()
        if media is not None and media.complete:
            yield from media.biased_content.all()

        media = BiasedMedia.objects.create(url=url, name=name)
        # TODO: implement a way to find a sentence from the video

    def bias_from_text(self, text: str) -> BiasedContent:
        if bias := BiasedContent.objects.filter(content=text).first():
            return bias

        
