from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session
