from datetime import UTC

from app.core.audit import create_safety_audit
from app.core.safety import RiskLevel, evaluate_safety


def test_audit_records_trigger_timestamp_and_ticket() -> None:
    result = evaluate_safety("Vedo fumo")
    audit = create_safety_audit("Vedo fumo", result, ticket_id="T-42")

    assert audit.ticket_id == "T-42"
    assert audit.timestamp.tzinfo is UTC
    assert audit.trigger_reasons == result.trigger_reasons
    assert audit.result == "blocked"
    assert audit.risk_level is RiskLevel.IMMEDIATE_STOP


def test_audit_anonymizes_email_and_phone() -> None:
    text = "Scrivere a mario@example.com o chiamare +39 333 123 4567: vedo fumo"
    audit = create_safety_audit(text, evaluate_safety(text))

    assert "mario@example.com" not in audit.anonymized_input
    assert "333 123 4567" not in audit.anonymized_input
    assert "[EMAIL]" in audit.anonymized_input
    assert "[PHONE]" in audit.anonymized_input
