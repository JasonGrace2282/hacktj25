from typing import Annotated

from celery import shared_task
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from pydantic_core import from_json

from .models import BiasedContent



type zero_to_one = Annotated[float, Field(ge=0, le=1)]

class CheckBSResponse(BaseModel):
    misinformation_amount: zero_to_one
    certainity: zero_to_one
