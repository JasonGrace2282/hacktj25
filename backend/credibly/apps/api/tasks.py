from typing import Annotated

from celery import shared_task
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from .models import BiasedContent


@shared_task
def check_validity_of_info(info: str, content_id: int):
    """Sets the accuracy of the content based on the validity of the info."""
    content = BiasedContent.objects.get(id=content_id)

    gemini = genai.Client(api_key="AIzaSyCoFeqRzGX9VUr6OJHWZJxbkpV54oGt0-g")
    response = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            "What is the amount of misinformation in this statement, on a scale of 0 to 1?"
            f"How certain are you in your decision on a scale of 0 to 1?\n{info!r}"
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CheckBSResponse,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    if isinstance(response.parsed, dict):
        parsed = CheckBSResponse.model_validate_json(response.parsed)
    else:
        parsed = response.parsed
    assert isinstance(parsed, CheckBSResponse)

    print("Gemini info: ", parsed)
    if parsed.certainity < 0.5:
        return

    content.accuracy = 1 - parsed.misinformation_amount
    content.save(update_fields=["accuracy"])


type zero_to_one = Annotated[float, Field(ge=0, le=1)]

class CheckBSResponse(BaseModel):
    misinformation_amount: zero_to_one
    certainity: zero_to_one
