from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailClassificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    urgency: int
    requires_attention: bool
    short_summary: str
    suggested_reply: str | None
    confidence: int


class EmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str | None
    sender: str | None
    received_at: datetime | None
    snippet: str | None
    is_unread: bool


class EmailResponse(EmailOut):
    body: str | None = None
    classification: EmailClassificationOut | None = None


class EmailListResponse(BaseModel):
    emails: list[EmailOut]


class EmailClassificationResponse(EmailClassificationOut):
    pass
