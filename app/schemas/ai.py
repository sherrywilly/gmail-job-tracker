from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    email: str = Field(min_length=1, max_length=200_000)


class ClassifyResponse(BaseModel):
    result: dict
