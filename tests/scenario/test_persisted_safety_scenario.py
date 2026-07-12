from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent, SafetyAssessment
from app.services.ticket_service import add_inbound_message, create_ticket


async def test_water_on_board_scenario_is_blocked_persisted_and_not_sent(
    db_session: AsyncSession,
) -> None:
    ticket = await create_ticket(db_session, "Acqua sulla scheda")
    result = await add_inbound_message(
        db_session,
        ticket.id,
        "È entrata acqua sulla scheda",
        "scenario-water-1",
    )
    assessment = await db_session.scalar(
        select(SafetyAssessment).where(SafetyAssessment.ticket_id == ticket.id)
    )
    audit = await db_session.scalar(
        select(AuditEvent).where(AuditEvent.ticket_id == ticket.id)
    )

    assert assessment is not None
    assert assessment.workflow_blocked is True
    assert assessment.requires_human_review is True
    assert audit is not None
    assert audit.action == "safety_evaluated"
    assert result.customer_message_sent is False
