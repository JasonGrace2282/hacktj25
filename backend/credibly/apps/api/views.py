import contextlib
import os
import tempfile
from pydantic import Field
from typing import Annotated
import pydantic
import whisper
import moviepy
import yt_dlp
import easyocr
import cv2

from django.http import JsonResponse
from pydantic_core._pydantic_core import from_json
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from django.db import models
from textblob import TextBlob


from .models import BiasedContent
from .forms import MediaDataForm
from .serializers import (
    BiasedContentSerializer,
    BiasedMediaSerializer,
    ContentCreatorSerializer,
)
from .models import ContentCreator, BiasedMedia
from google.genai import types
import google.genai as genai


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
def start_analysis_of_statements(request, url):
    m = BiasedMedia.objects.get(url=url)
    if not m.biased_content.exclude(accuracy_isnull=True).exists():
        for content in m.biased_content.all():
            check_validity_of_info(content)
    contents = m.biased_content.filter(accuracy__isnull=False).all()

    return JsonResponse(
        {
            "contents": BiasedContentSerializer(m.biased_content.all(), many=True).data,
            "average_misinformation": 1 - sum([c.accuracy for c in contents]) / len(contents),
        }
    )


def check_validity_of_info(content: BiasedContent):
    """Sets the accuracy of the content based on the validity of the info."""
    info = content.content

    prompt = (
        "{"
        '\t"misinformation_score": "What is the amount of misinformation in this statement, on a scale of 0 to 1?",'
        '\t"certainty_score": "How certain are you in your decision on a scale of 0 to 1?"'
        "}\n"
        f"The output should strictly follow the JSON schema: {CheckBSResponse.model_json_schema()}\n"
        f"The input statement is: {info!r}\n"
        "Please provide the output strictly in JSON format, and do not include any additional information or analysis."
    )

    gemini = genai.Client(api_key="AIzaSyCoFeqRzGX9VUr6OJHWZJxbkpV54oGt0-g")
    response = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    if response.candidates is None:
        print("GEMINI GOT COOKED GODDAMN IT")
        return

    gemini_content = response.candidates[0].content
    if gemini_content is None or gemini_content.parts is None:
        print("I'm gonna jump off a cliff FUK\n", response)
        return

    text = gemini_content.parts[0].text
    if text is None:
        print("I give up ", response)
        return

    text = text.strip("`").removeprefix("json")
    parsed = CheckBSResponse.model_validate(from_json(text, allow_partial=True))

    print("Gemini info: ", parsed)
    if parsed.certainity < 0.5:
        print("Gemini not sure")
        return

    content.accuracy = 1 - parsed.misinformation_amount
    content.accuracy_certainity = parsed.certainity
    content.save(update_fields=["accuracy"])


type zero_to_one = Annotated[float, Field(ge=0, le=1)]


class CheckBSResponse(pydantic.BaseModel):
    misinformation_amount: zero_to_one
    certainity: zero_to_one


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

    return JsonResponse(
        {
            "average_bias": avg_bias,
            "contents": BiasedContentSerializer(media_content, many=True).data,
        }
    )


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
        print(f"{sentence.raw}: {content.bias_strength}")
    return contents
