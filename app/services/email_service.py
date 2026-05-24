from sqlalchemy import Select, desc, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email


async def list_emails_for_user(
    db: AsyncSession,
    user_id: int,
    unread_only: bool,
    limit: int,
    offset: int,
) -> list[Email]:
    stmt: Select[tuple[Email]] = select(Email).where(Email.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Email.is_unread.is_(True))
    stmt = stmt.order_by(desc(Email.received_at), desc(Email.id)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_email_for_user(db: AsyncSession, user_id: int, email_id: int) -> Email | None:
    stmt = (
        select(Email)
        .where(Email.user_id == user_id, Email.id == email_id)
        .options(selectinload(Email.classification))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_urgent_emails(db: AsyncSession, user_id: int, limit: int) -> list[Email]:
    stmt = (
        select(Email)
        .where(Email.user_id == user_id)
        .where(Email.is_unread.is_(True))
        .order_by(desc(Email.received_at), desc(Email.id))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
