import contextlib
import os
import tempfile
from collections.abc import Iterator

from channels.generic.websocket import JsonWebsocketConsumer, WebsocketConsumer
from textblob import TextBlob
from rest_framework.renderers import JSONRenderer
import whisper
import moviepy
import yt_dlp
import easyocr
import cv2

from .models import BiasedContent, BiasedMedia
from .serializers import BiasedContentSerializer, BiasedMediaSerializer

reader = easyocr.Reader(["en"])
audio_model = whisper.load_model("tiny")


class Credibility(WebsocketConsumer):
    def connect(self):
        url_kw = self.scope["url_route"]["kwargs"]
        self.name = url_kw["name"]
        self.url = url_kw["url"]
        self.accept()

        audio_text = None
        video_text = {}

        print("Starting video processing")
        video_id = yt_dlp.YoutubeDL().extract_info(self.url)["id"]
        temp_video = os.path.join(tempfile.gettempdir(), video_id) + ".mp4"

        with yt_dlp.YoutubeDL({"outtmpl": temp_video}) as ydl:
            ydl.extract_info(self.url, download=True)

        print("Extracted video info")
        encoded_video = moviepy.VideoFileClip(temp_video)
        temp_audio = os.path.join(tempfile.gettempdir(), video_id) + ".wav"
        encoded_video.audio.write_audiofile(temp_audio)

        print("Transscribing")
        with contextlib.redirect_stdout(None):
            transcribed_audio = audio_model.transcribe(temp_audio)

            lines = []

            for segment in transcribed_audio['segments']:
                time_duration = segment['end'] - segment['start']
                lines.append(f"{time_duration:.2f}s: {segment['text'].strip()}")

            audio_text = "\n".join(lines)

            for t in range(0, encoded_video.n_frames, int(encoded_video.fps)):
                frame = encoded_video.get_frame(t)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                results = reader.readtext(frame, detail=0)
                if results:
                    video_text[t / int(encoded_video.fps)] = results

            video_text = "\n".join([f"{time}: {line}" for time, line in video_text.items()])

        media = BiasedMedia.objects.filter(url=self.url).first()
        if media is not None and media.complete:
            media_content: Iterator[BiasedContent] = media.biased_content.all()
        else:
            if media is None:
                media = BiasedMedia.objects.create(url=self.url, name=self.name)
            media_content = self.bias_from_text(audio_text, media)

        print("FOUND MEDIA CONTENT YIPEEEEEEEEEEEE")

        for content in media_content:
            ser = BiasedContentSerializer(content)
            print(ser.data)
            self.send(bytes_data=JSONRenderer().render(ser.data))
        media.complete = True
        media.save()
        self.close(reason="video processing complete")

    def bias_from_text(self, text: str, media: BiasedMedia) -> Iterator[BiasedContent]:
        print("PREBLOB")
        blob = TextBlob(text)
        print("POSTBLOB")
        for sentence in blob.sentences:
            content = BiasedContent.objects.create(
                media=media,
                content=sentence.raw,
                bias_strength=sentence.sentiment.subjectivity,
                accuracy=None,
            )
            yield content


class GeneralInfo(JsonWebsocketConsumer):
    def receive_json(self, json_data):
        data = json_data.get("url")
        if data is None:
            return
        media = BiasedMedia.objects.get(url=data)
        ser = BiasedMediaSerializer(media)
        self.send_json(JSONRenderer().render(ser.data))
