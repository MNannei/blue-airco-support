import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionFactory


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        await session.execute(
            text(
                "TRUNCATE audit_events, safety_assessments, messages, tickets, "
                "product_units, vessels, contacts, customers, users, webhook_events CASCADE"
            )
        )
        await session.commit()
        yield session
        await session.rollback()
