from app.core.safety import RiskLevel
from app.services.safety_service import assess_message


def test_critical_message_blocks_workflow_and_creates_audit() -> None:
    assessment = assess_message("Vedo scintille", ticket_id="T-7")

    assert assessment.safety_result.blocks_workflow is True
    assert assessment.safety_result.requires_human_escalation is True
    assert assessment.audit.ticket_id == "T-7"
    assert assessment.audit.result == "blocked"
    assert assessment.customer_message_sent is False


def test_warning_requires_review_without_immediate_stop() -> None:
    assessment = assess_message("Il motore è surriscaldato")

    assert assessment.safety_result.risk_level is RiskLevel.WARNING
    assert assessment.safety_result.blocks_workflow is False
    assert assessment.safety_result.requires_human_escalation is True
    assert assessment.customer_message_sent is False


def test_ordinary_message_is_audited_without_sending_response() -> None:
    assessment = assess_message("Vorrei fissare una manutenzione")

    assert assessment.safety_result.risk_level is RiskLevel.NONE
    assert assessment.audit.result == "allowed_with_controls"
    assert assessment.customer_message_sent is False
