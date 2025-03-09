from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from .forms import MediaDataForm
from .serializers import BiasedMediaSerializer


@api_view(["GET"])
def get_video(request, video_url):
    form = MediaDataForm(request.GET)
    if not form.is_valid():
        return JsonResponse(
            {"error": "Invalid data", "errors": form.errors.as_json()}, status=400
        )
    media = form.cleaned_data["media"]
    ser = BiasedMediaSerializer(media)
    return JsonResponse(ser.data)
