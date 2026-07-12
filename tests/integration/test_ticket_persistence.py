import asyncio
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionFactory
from app.models import AuditEvent, Message, ProductUnit, SafetyAssessment, Ticket
from app.services.ticket_service import (
    SafetyPersistenceError,
    add_inbound_message,
    create_ticket,
)


async def test_ticket_message_safety_and_audit_are_persisted(
    db_session: AsyncSession,
) -> None:
    ticket = await create_ticket(db_session, "Assistenza")
    result = await add_inbound_message(
        db_session,
        ticket.id,
        "Vedo fumo, contatto mario@example.com",
        "ext-1",
    )

    assessment = await db_session.scalar(
        select(SafetyAssessment).where(SafetyAssessment.ticket_id == ticket.id)
    )
    audit = await db_session.scalar(
        select(AuditEvent).where(AuditEvent.ticket_id == ticket.id)
    )
    persisted_ticket = await db_session.get(Ticket, ticket.id)

    assert result.customer_message_sent is False
    assert assessment is not None
    assert assessment.workflow_blocked is True
    assert assessment.requires_human_review is True
    assert "mario@example.com" not in assessment.anonymized_input
    assert audit is not None
    assert audit.action == "safety_evaluated"
    assert persisted_ticket is not None
    assert persisted_ticket.status == "safety_blocked"


async def test_external_message_id_is_idempotent_and_audited(
    db_session: AsyncSession,
) -> None:
    ticket = await create_ticket(db_session, "Idempotenza")
    first = await add_inbound_message(db_session, ticket.id, "Messaggio ordinario", "same-id")
    second = await add_inbound_message(db_session, ticket.id, "Messaggio ordinario", "same-id")

    count = await db_session.scalar(
        select(func.count()).select_from(Message).where(Message.external_message_id == "same-id")
    )
    duplicate_audit = await db_session.scalar(
        select(AuditEvent).where(AuditEvent.action == "duplicate_message_ignored")
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert first.message.id == second.message.id
    assert count == 1
    assert duplicate_audit is not None


async def test_concurrent_duplicate_is_constrained_by_database(
    db_session: AsyncSession,
) -> None:
    ticket = await create_ticket(db_session, "Concorrenza")

    async def ingest() -> bool:
        async with AsyncSessionFactory() as session:
            result = await add_inbound_message(session, ticket.id, "Richiesta", "concurrent-id")
            return result.duplicate

    duplicates = await asyncio.gather(ingest(), ingest())
    db_session.expire_all()
    count = await db_session.scalar(
        select(func.count()).select_from(Message).where(Message.external_message_id == "concurrent-id")
    )

    assert sorted(duplicates) == [False, True]
    assert count == 1


async def test_product_unit_can_be_linked_to_ticket(db_session: AsyncSession) -> None:
    unit = ProductUnit(serial_number="BA-001", model_name="Blue Airco Unit", status="active")
    db_session.add(unit)
    await db_session.commit()
    await db_session.refresh(unit)

    ticket = await create_ticket(db_session, "Unità collegata", product_unit_id=unit.id)

    assert ticket.product_unit_id == unit.id


async def test_audit_event_is_immutable(db_session: AsyncSession) -> None:
    ticket = await create_ticket(db_session, "Audit")
    await add_inbound_message(db_session, ticket.id, "Vedo fumo", "audit-id")
    audit = await db_session.scalar(select(AuditEvent).where(AuditEvent.ticket_id == ticket.id))
    assert audit is not None

    audit.action = "tampered"
    with pytest.raises(ValueError, match="immutable"):
        await db_session.commit()
    await db_session.rollback()


async def test_safety_persistence_error_preserves_ticket_and_message(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticket = await create_ticket(db_session, "Errore persistenza")
    monkeypatch.setattr(
        "app.services.ticket_service.persist_safety_evaluation",
        AsyncMock(side_effect=SQLAlchemyError("simulated")),
    )

    with pytest.raises(SafetyPersistenceError):
        await add_inbound_message(db_session, ticket.id, "Vedo fumo", "failure-id")

    persisted_ticket = await db_session.get(Ticket, ticket.id)
    message = await db_session.scalar(
        select(Message).where(Message.external_message_id == "failure-id")
    )
    failure_audit = await db_session.scalar(
        select(AuditEvent).where(AuditEvent.action == "safety_persistence_failed")
    )

    assert persisted_ticket is not None
    assert persisted_ticket.status == "safety_persistence_error"
    assert message is not None
    assert failure_audit is not None
