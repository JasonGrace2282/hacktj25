from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from django.db import models

from .forms import MediaDataForm
from .serializers import BiasedMediaSerializer, ContentCreatorSerializer
from .models import ContentCreator, BiasedMedia
from .tasks import check_validity_of_info


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
            "creators": [renderer.render(ContentCreatorSerializer(creators, many=True).data)],
            "media": [renderer.render(BiasedMediaSerializer(media, many=True).data)],
        },
    )


@api_view(["POST"])
def start_analysis_of_statements(request, video_url: str):
    m = BiasedMedia.objects.get(url=video_url)
    for content in m.biased_content.all():
        check_validity_of_info.delay(content.id)
    return JsonResponse({"status": "Analysis started"})
