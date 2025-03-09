import os

from celery import shared_task
from newsapi import NewsApiClient

from .models import BiasedContent



@shared_task
def check_validity_of_info(info: str, content_id: int):
    """Sets the accuracy of the content based on the validity of the info."""
    # TODO: figure out if the info is trying to state a fact

    content = BiasedContent.objects.get(id=content_id)
    api_key = os.environ.get('NEWS_API_KEY')
    if not api_key:
        raise ValueError('NEWS_API_KEY environment variable not set')
    client = NewsApiClient(api_key=api_key)
