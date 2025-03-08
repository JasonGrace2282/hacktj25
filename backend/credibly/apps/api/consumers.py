from collections.abc import Iterator
from channels.generic.websocket import WebsocketConsumer
from textblob import TextBlob
from rest_framework.renderers import JSONRenderer

from .models import BiasedContent, BiasedMedia
from .serializers import BiasedContentSerializer


class Credibility(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        # TODO: figure out how to extract info
        media = BiasedMedia.objects.filter(url=url).first()
        if media is not None and media.complete:
            yield from media.biased_content.all()

        media = BiasedMedia.objects.create(url=url, name=name)


    def find_biased_content(self, name: str, url: str) -> Iterator[BiasedContent]:
        # TODO: implement a way to find all the text from the video
        text = (
            "Beautiful is better than ugly. "
            "Explicit is better than implicit. "
            "Simple is better than complex."
        )
        for biased_content in self.bias_from_text(text):
            biased_content.media = media
            biased_content.save()

            yield biased_content

    def bias_from_text(self, text: str) -> Iterator[BiasedContent]:
        blob = TextBlob(text)
