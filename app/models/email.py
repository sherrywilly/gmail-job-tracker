from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (UniqueConstraint("user_id", "message_id", name="uq_user_message_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    message_id: Mapped[str] = mapped_column(String(128), index=True)
    thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sender: Mapped[str | None] = mapped_column(String(512), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_unread: Mapped[bool] = mapped_column(Boolean, default=True)
    labels: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    classification: Mapped[Optional[EmailClassification]] = relationship(
        back_populates="email",
        uselist=False,
        lazy="selectin",
    )


class EmailClassification(Base):
    __tablename__ = "email_classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), unique=True, index=True)

    category: Mapped[str] = mapped_column(String(64))
    urgency: Mapped[int] = mapped_column(Integer)
    requires_attention: Mapped[bool] = mapped_column(Boolean, default=False)
    short_summary: Mapped[str] = mapped_column(Text)
    suggested_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer)  # stored as 0-100

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    email: Mapped[Email] = relationship(back_populates="classification")
