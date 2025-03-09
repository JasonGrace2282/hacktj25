from typing import Annotated

from celery import shared_task
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from pydantic_core import from_json

from .models import BiasedContent


@shared_task
def check_validity_of_info(content_id: int):
    """Sets the accuracy of the content based on the validity of the info."""
    content = BiasedContent.objects.get(id=content_id)
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

class CheckBSResponse(BaseModel):
    misinformation_amount: zero_to_one
    certainity: zero_to_one
