from django.urls import path

from . import views

urlpatterns = [
    path("analysis/<path:video_url>", views.start_analysis_of_statements),
]
