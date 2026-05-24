from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.db.session import engine


async def init_db(db_engine: AsyncEngine | None = None) -> None:
    # Ensure models are imported so SQLAlchemy can register them on Base.metadata.
    from app.models import email as _email  # noqa: F401
    from app.models import user as _user  # noqa: F401

    target_engine = db_engine or engine
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
