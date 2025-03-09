import os
import tempfile
from collections.abc import Iterator

from channels.generic.websocket import WebsocketConsumer
from textblob import TextBlob
from rest_framework.renderers import JSONRenderer
import whisper
import moviepy
import yt_dlp
import easyocr
import cv2
# manually installed: easyocr, openai-whisper

from .models import BiasedContent, BiasedMedia
from .serializers import BiasedContentSerializer
from .tasks import check_validity_of_info

reader = easyocr.Reader(["en"])


class Credibility(WebsocketConsumer):
    def connect(self):
        url_kw = self.scope["url_route"]["kwargs"]
        self.name = url_kw["name"]
        self.url = url_kw["url"]
        self.accept()

        audio_text = None
        video_text = []

        # Initialize whisper model when needed
        audio_model = whisper.load_model("base")

        video_id = yt_dlp.YoutubeDL().extract_info(self.url)["id"]
        temp_video = os.path.join(tempfile.gettempdir(), video_id) + ".mp4"

        with yt_dlp.YoutubeDL({"outtmpl": temp_video}) as ydl:
            ydl.extract_info(self.url, download=True)

        encoded_video = moviepy.VideoFileClip(temp_video)
        temp_audio = os.path.join(tempfile.gettempdir(), video_id) + ".wav"
        encoded_video.audio.write_audiofile(temp_audio)

        transcribed_audio = audio_model.transcribe(temp_audio)

        audio_text = transcribed_audio

        for t in range(0, encoded_video.n_frames, encoded_video.fps):
            frame = encoded_video.get_frame(t)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            results = reader.readtext(frame, detail=0)
            if results:
                video_text.append((t / encoded_video.fps, results))

        media = BiasedMedia.objects.filter(url=self.url).first()
        if media is not None and media.complete:
            media_content: Iterator[BiasedContent] = media.biased_content.all()
        else:
            if media is None:
                media = BiasedMedia.objects.create(url=self.url, name=self.name)
            media_content = self.bias_from_text(audio_text, media)

        for content in media_content:
            ser = BiasedContentSerializer(content)
            self.send(bytes_data=JSONRenderer().render(ser.data))
        media.complete = True
        media.save()
        self.close(reason="video processing complete")

    def bias_from_text(self, text: str, media: BiasedMedia) -> Iterator[BiasedContent]:
        blob = TextBlob(text)
        for sentence in blob.sentences:
            content = BiasedContent.objects.create(
                media=media,
                content=sentence.raw,
                bias_strength=sentence.sentiment.subjectivity,
                accuracy=None,
            )
            check_validity_of_info.delay(sentence.raw, content.id)
            yield content
