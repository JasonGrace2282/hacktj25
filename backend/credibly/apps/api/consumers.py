from collections.abc import Iterator
from channels.generic.websocket import WebsocketConsumer
from textblob import TextBlob
from rest_framework.renderers import JSONRenderer

from .models import BiasedContent, BiasedMedia
from .serializers import BiasedContentSerializer


class Credibility(WebsocketConsumer):
    def connect(self):
        url_kw = self.scope["url_route"]["kwargs"]
        self.name = url_kw["name"]
        self.url = url_kw["url"]
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        # can't process bytes
        if text_data is None:
            return

        media = BiasedMedia.objects.filter(url=self.url).first()
        if media is not None and media.complete:
            media_content: Iterator[BiasedContent] = media.biased_content.all()
        else:
            media = BiasedMedia.objects.create(url=self.url, name=self.name)
            media_content = self.find_biased_content(media)

        for content in media_content:
            ser = BiasedContentSerializer(content)
            self.send(bytes_data=JSONRenderer().render(ser.data))
        self.close(reason="video processing complete")

    def find_biased_content(self, media: BiasedMedia) -> Iterator[BiasedContent]:
        # TODO: implement a way to find all the text from the video
        text = (
            "Beautiful is better than ugly. "
            "Explicit is better than implicit. "
            "Simple is better than complex."
        )
        yield from self.bias_from_text(text, media)

    def bias_from_text(self, text: str, media: BiasedMedia) -> Iterator[BiasedContent]:
        blob = TextBlob(text)
        for sentence in blob.sentences:
            yield BiasedContent(
                media=media,
                content=sentence.raw,
                bias_strength=sentence.sentiment.subjectivity,
                accuracy=None,
            )
