from django.urls import path

from . import views

urlpatterns = [
    path("analysis/", views.start_analysis_of_statements),
    path("credibility/", views.credibility_view),
]
