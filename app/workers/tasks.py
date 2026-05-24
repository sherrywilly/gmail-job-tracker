import logging
from datetime import UTC, datetime

from app.workers.celery_app import celery_app
from sqlalchemy import desc, select

from app.db.session import SessionLocal
from app.models.email import Email
from app.models.user import User
from app.services import gmail_service
from app.services.notification_service import send_daily_digest


log = logging.getLogger(__name__)


def enqueue_sync_inbox(user_id: int) -> None:
    sync_gmail_inbox.delay(user_id=user_id)


@celery_app.task(name="app.workers.tasks.sync_gmail_inbox")
def sync_gmail_inbox(user_id: int) -> None:
    if not gmail_service.is_enabled():
        log.info("Gmail integration not configured; skipping sync.")
        return

    messages = gmail_service.list_recent_messages(max_results=25)
    message_ids = [m.get("id") for m in messages if m.get("id")]
    if not message_ids:
        return

    async def _run() -> None:
        async with SessionLocal() as db:
            for mid in message_ids:
                existing = await db.execute(select(Email).where(Email.user_id == user_id, Email.message_id == mid))
                if existing.scalar_one_or_none() is not None:
                    continue

                msg = gmail_service.get_message(mid)
                if not msg:
                    continue
                fields = gmail_service.extract_email_fields(msg)
                email = Email(
                    user_id=user_id,
                    message_id=fields["message_id"],
                    thread_id=fields.get("thread_id"),
                    subject=fields.get("subject"),
                    sender=fields.get("sender"),
                    received_at=fields.get("received_at"),
                    snippet=fields.get("snippet"),
                    body=fields.get("body"),
                    labels=fields.get("labels"),
                    is_unread=fields.get("is_unread", True),
                    created_at=datetime.now(UTC),
                )
                db.add(email)
            await db.commit()

    import asyncio

    asyncio.run(_run())


@celery_app.task(name="app.workers.tasks.daily_digest")
def daily_digest() -> None:
    async def _run() -> None:
        async with SessionLocal() as db:
            users = (await db.execute(select(User))).scalars().all()
            for user in users:
                stmt = (
                    select(Email)
                    .where(Email.user_id == user.id)
                    .where(Email.is_unread.is_(True))
                    .order_by(desc(Email.received_at), desc(Email.id))
                    .limit(50)
                )
                emails = (await db.execute(stmt)).scalars().all()
                if emails:
                    send_daily_digest(user.email, list(emails))

    import asyncio

    asyncio.run(_run())
