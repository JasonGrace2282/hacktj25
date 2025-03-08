import os
import tempfile
from collections.abc import Iterator
from channels.generic.websocket import WebsocketConsumer
from textblob import TextBlob
import requests
from rest_framework.renderers import JSONRenderer
import whisper
import moviepy
import yt_dlp
import easyocr
import cv2
# manually installed: easyocr, whisper

from .models import BiasedContent, BiasedMedia
from .serializers import BiasedContentSerializer

audio_model = whisper.load_model("base")
reader = easyocr.Reader(['en'])

class Credibility(WebsocketConsumer):
    def connect(self):
        url_kw = self.scope["url_route"]["kwargs"]
        self.name = url_kw["name"]
        self.url = url_kw["url"]
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        # TODO: figure out how to extract info
        audio_text = None
        video_text = []

        if bytes_data:
            url = "https://www.tiktok.com/@faroukiie/video/7458768121059396894?is_from_webapp=1&sender_device=pc"
            videoId = yt_dlp.YoutubeDL().extract_info(url)["id"]
            temp_video = os.path.join(tempfile.gettempdir(), videoId) + ".mp4"

            with yt_dlp.YoutubeDL({"outtmpl": temp_video}) as ydl:
                info_dict = ydl.extract_info(url, download=True)

            encoded_video = moviepy.VideoFileClip(temp_video)
            temp_audio = os.path.join(tempfile.gettempdir(), videoId) + ".wav"
            encoded_video.audio.write_audiofile(temp_audio)

            transcribed_audio = audio_model.transcribe(temp_audio)

            audio_text = transcribed_audio

            for t in range(0, encoded_video.n_frames, encoded_video.fps):
                frame = encoded_video.get_frame(t)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                results = reader.readtext(frame, detail=0)
                if results:
                    video_text.append((t / encoded_video.fps, results))


        media = BiasedMedia.objects.filter(url=url).first()
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
            yield BiasedContent.objects.create(
                media=media,
                content=sentence.raw,
                bias_strength=sentence.sentiment.subjectivity,
                accuracy=None,
            )
