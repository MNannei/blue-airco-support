"""Application service for safety evaluation and audit creation."""

from dataclasses import dataclass

from app.core.audit import SafetyAuditRecord, create_safety_audit
from app.core.safety import SafetyResult, evaluate_safety


@dataclass(frozen=True)
class SafetyAssessment:
    safety_result: SafetyResult
    audit: SafetyAuditRecord
    customer_message_sent: bool = False


def assess_message(text: str, ticket_id: str | None = None) -> SafetyAssessment:
    safety_result = evaluate_safety(text)
    audit = create_safety_audit(text, safety_result, ticket_id=ticket_id)
    return SafetyAssessment(safety_result=safety_result, audit=audit)
