from collections.abc import AsyncIterator

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.main import app


async def test_internal_ticket_api_persists_safety_and_audit(
    db_session: AsyncSession,
) -> None:
    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            created = await client.post("/internal/tickets", json={"subject": "API ticket"})
            assert created.status_code == 201
            ticket_id = created.json()["id"]

            message = await client.post(
                f"/internal/tickets/{ticket_id}/messages",
                json={"text": "Sento odore di bruciato", "external_message_id": "api-1"},
            )
            fetched = await client.get(f"/internal/tickets/{ticket_id}")
            audit = await client.get(f"/internal/tickets/{ticket_id}/audit")
    finally:
        app.dependency_overrides.clear()

    assert message.status_code == 201
    assert message.json()["workflow_blocked"] is True
    assert message.json()["requires_human_review"] is True
    assert message.json()["customer_message_sent"] is False
    assert fetched.json()["status"] == "safety_blocked"
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "safety_evaluated"
