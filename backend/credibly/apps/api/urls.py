from django.urls import path

from . import views

urlpatterns = [
    path("analysis/<path:url>", views.start_analysis_of_statements),
    path("credibility/<path:url>", views.credibility_view),
]
