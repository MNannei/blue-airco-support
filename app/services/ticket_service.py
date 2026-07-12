"""Transactional ticket operations; no outbound customer communication."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import anonymize_input
from app.core.safety import RiskLevel, SafetyResult, evaluate_safety
from app.models import AuditEvent, Message, ProductUnit, SafetyAssessment, Ticket


class TicketNotFoundError(LookupError):
    pass


class ProductUnitNotFoundError(LookupError):
    pass


class SafetyPersistenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class AddMessageResult:
    message: Message
    safety_assessment: SafetyAssessment | None
    duplicate: bool
    customer_message_sent: bool = False


def ticket_status_for_safety(result: SafetyResult) -> str:
    if result.risk_level is RiskLevel.IMMEDIATE_STOP:
        return "safety_blocked"
    if result.risk_level is RiskLevel.WARNING:
        return "requires_human_review"
    return "open"


async def create_ticket(
    session: AsyncSession,
    subject: str,
    customer_id: UUID | None = None,
    product_unit_id: UUID | None = None,
) -> Ticket:
    if product_unit_id is not None and await session.get(ProductUnit, product_unit_id) is None:
        raise ProductUnitNotFoundError(str(product_unit_id))
    ticket = Ticket(
        subject=subject,
        customer_id=customer_id,
        product_unit_id=product_unit_id,
        status="open",
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def get_ticket(session: AsyncSession, ticket_id: UUID) -> Ticket:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(str(ticket_id))
    return ticket


async def get_ticket_audit(session: AsyncSession, ticket_id: UUID) -> list[AuditEvent]:
    await get_ticket(session, ticket_id)
    result = await session.scalars(
        select(AuditEvent)
        .where(AuditEvent.ticket_id == ticket_id)
        .order_by(AuditEvent.created_at, AuditEvent.id)
    )
    return list(result)


async def persist_safety_evaluation(
    session: AsyncSession,
    ticket: Ticket,
    message: Message,
    text: str,
) -> SafetyAssessment:
    result = evaluate_safety(text)
    anonymized = anonymize_input(text)
    assessment = SafetyAssessment(
        ticket_id=ticket.id,
        message_id=message.id,
        risk_level=result.risk_level.value,
        requires_human_review=result.requires_human_escalation,
        workflow_blocked=result.blocks_workflow,
        anonymized_input=anonymized,
        trigger_reasons=list(result.trigger_reasons),
        status="completed",
    )
    session.add(assessment)
    await session.flush()
    session.add(
        AuditEvent(
            ticket_id=ticket.id,
            safety_assessment_id=assessment.id,
            actor_type="system",
            action="safety_evaluated",
            status="recorded",
            metadata_json={
                "anonymized_input": anonymized,
                "risk_level": result.risk_level.value,
                "requires_human_review": result.requires_human_escalation,
                "workflow_blocked": result.blocks_workflow,
                "trigger_reasons": list(result.trigger_reasons),
            },
        )
    )
    ticket.status = ticket_status_for_safety(result)
    await session.commit()
    await session.refresh(assessment)
    return assessment


async def add_inbound_message(
    session: AsyncSession,
    ticket_id: UUID,
    text: str,
    external_message_id: str,
) -> AddMessageResult:
    ticket = await get_ticket(session, ticket_id)
    existing = await session.scalar(
        select(Message).where(Message.external_message_id == external_message_id)
    )
    if existing is not None:
        await _record_duplicate(session, ticket_id, external_message_id)
        return AddMessageResult(existing, None, duplicate=True)

    message = Message(
        ticket_id=ticket_id,
        external_message_id=external_message_id,
        direction="inbound",
        body=text,
        status="received",
    )
    session.add(message)
    try:
        await session.commit()
        await session.refresh(message)
    except IntegrityError:
        await session.rollback()
        existing = await session.scalar(
            select(Message).where(Message.external_message_id == external_message_id)
        )
        if existing is None:
            raise
        await _record_duplicate(session, ticket_id, external_message_id)
        return AddMessageResult(existing, None, duplicate=True)

    try:
        assessment = await persist_safety_evaluation(session, ticket, message, text)
    except SQLAlchemyError as exc:
        await session.rollback()
        preserved_ticket = await get_ticket(session, ticket_id)
        preserved_ticket.status = "safety_persistence_error"
        session.add(
            AuditEvent(
                ticket_id=ticket_id,
                actor_type="system",
                action="safety_persistence_failed",
                status="recorded",
                metadata_json={"external_message_id": external_message_id},
            )
        )
        await session.commit()
        raise SafetyPersistenceError("Safety persistence failed; ticket preserved") from exc

    return AddMessageResult(message, assessment, duplicate=False)


async def _record_duplicate(
    session: AsyncSession, ticket_id: UUID, external_message_id: str
) -> None:
    session.add(
        AuditEvent(
            ticket_id=ticket_id,
            actor_type="system",
            action="duplicate_message_ignored",
            status="recorded",
            metadata_json={"external_message_id": external_message_id},
        )
    )
    await session.commit()
