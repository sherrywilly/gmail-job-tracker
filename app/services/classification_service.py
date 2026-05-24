from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email, EmailClassification
from app.services.ai_service import classify_text


async def classify_and_store_email(db: AsyncSession, email: Email) -> EmailClassification:
    text = email.body or email.snippet or ""
    result = await classify_text(text)

    category = str(result.get("category") or "Requires Attention")
    urgency = int(result.get("urgency") or 5)
    urgency = max(1, min(10, urgency))

    requires_attention = bool(result.get("requires_attention") if "requires_attention" in result else urgency >= 7)
    short_summary = str(result.get("short_summary") or "")[:2000] or (text[:280] or "No content")
    suggested_reply = result.get("suggested_reply")
    suggested_reply = str(suggested_reply)[:8000] if suggested_reply else None

    confidence = int(result.get("confidence") or 50)
    confidence = max(0, min(100, confidence))

    stmt = select(EmailClassification).where(EmailClassification.email_id == email.id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    now = datetime.now(UTC)

    if existing is None:
        existing = EmailClassification(
            email_id=email.id,
            category=category,
            urgency=urgency,
            requires_attention=requires_attention,
            short_summary=short_summary,
            suggested_reply=suggested_reply,
            confidence=confidence,
            created_at=now,
        )
        db.add(existing)
    else:
        existing.category = category
        existing.urgency = urgency
        existing.requires_attention = requires_attention
        existing.short_summary = short_summary
        existing.suggested_reply = suggested_reply
        existing.confidence = confidence

    await db.commit()
    await db.refresh(existing)
    return existing
