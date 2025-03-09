import contextlib
import os
import tempfile
from collections.abc import Iterator

import whisper
import moviepy
import yt_dlp
import easyocr
import cv2

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from django.db import models
from textblob import TextBlob


from .models import BiasedContent
from .forms import MediaDataForm
from .serializers import BiasedMediaSerializer, ContentCreatorSerializer
from .models import ContentCreator, BiasedMedia
from .tasks import check_validity_of_info


reader = easyocr.Reader(["en"])
audio_model = whisper.load_model("tiny")


@api_view(["GET"])
def get_video(request):
    form = MediaDataForm(request.GET)
    if not form.is_valid():
        return JsonResponse(
            {"error": "Invalid data", "errors": form.errors.as_json()}, status=400
        )
    media = form.cleaned_data["media"]
    ser = BiasedMediaSerializer(media)
    return JsonResponse(ser.data)


@api_view(["GET"])
def good_content_creators(request):
    creators = (
        ContentCreator.objects.annotate(
            avg_accuracy=models.Avg("media_set__biased_content__accuracy", default=0)
        )
        .filter(avg_accuracy__gte=0.5)
        .order_by("-avg_accuracy")
        .all()
    )
    media = BiasedMedia.objects.filter(content_creators__in=creators)
    renderer = JSONRenderer()
    return JsonResponse(
        request,
        {
            "creators": [
                renderer.render(ContentCreatorSerializer(creators, many=True).data)
            ],
            "media": [renderer.render(BiasedMediaSerializer(media, many=True).data)],
        },
    )


@api_view(["POST"])
def start_analysis_of_statements(request):
    m = BiasedMedia.objects.get(url=request.POST["video_url"])
    for content in m.biased_content.all():
        check_validity_of_info.delay(content.id)
    return JsonResponse({"status": "Analysis started"})


@api_view(["POST"])
def credibility_view(request, url):
    media = BiasedMedia.objects.filter(url=url).first()
    if media is not None and media.complete:
        media_content = media.biased_content.all()
    else:
        audio_text = None
        video_text = {}

        video_id = url[url.index("video/") + 6 :]
        print("Starting video processing")
        video_id = yt_dlp.YoutubeDL().extract_info(url)["id"]
        temp_video = os.path.join(tempfile.gettempdir(), video_id) + ".mp4"

        with yt_dlp.YoutubeDL({"outtmpl": temp_video}) as ydl:
            ydl.extract_info(url, download=True)

        print("Extracted video info")
        encoded_video = moviepy.VideoFileClip(temp_video)
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        encoded_video.audio.write_audiofile(temp_audio.name)

        print("Transcribing")
        with contextlib.redirect_stdout(None):
            transcribed_audio = audio_model.transcribe(temp_audio.name)

            lines = []

            for segment in transcribed_audio["segments"]:
                time_duration = segment["end"] - segment["start"]
                lines.append(f"{time_duration:.2f}s: {segment['text'].strip()}")

            audio_text = "\n".join(lines)

            for t in range(0, encoded_video.n_frames, int(encoded_video.fps)):
                frame = encoded_video.get_frame(t)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                results = reader.readtext(frame, detail=0)
                if results:
                    video_text[t / int(encoded_video.fps)] = results

            video_text = "\n".join(
                [f"{time}: {line}" for time, line in video_text.items()]
            )

        if media is None:
            media = BiasedMedia.objects.create(url=url, name="thing")
        media_content = bias_from_text(audio_text, media)

        temp_audio.close()
        os.remove(temp_video)

    media.complete = True
    media.save()
    avg_bias = sum([content.bias_strength for content in media_content]) / len(
        media_content
    )
    return JsonResponse(request, {"average_bias": avg_bias})


def bias_from_text(text: str, media: BiasedMedia) -> list[BiasedContent]:
    print("PREBLOB")
    blob = TextBlob(text)
    print("POSTBLOB")
    contents = []
    for sentence in blob.sentences:
        content = BiasedContent.objects.create(
            media=media,
            content=sentence.raw,
            bias_strength=sentence.sentiment.subjectivity,
            accuracy=None,
        )
        contents.append(content)
    return contents
