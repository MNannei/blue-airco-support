"""Structured in-memory audit records for safety evaluations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.safety import RiskLevel, SafetyResult


@dataclass(frozen=True)
class SafetyAuditRecord:
    timestamp: datetime
    ticket_id: str | None
    anonymized_input: str
    trigger_reasons: tuple[str, ...]
    result: str
    risk_level: RiskLevel


_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d .()-]{7,}\d)(?!\w)")


def anonymize_input(text: str) -> str:
    without_email = _EMAIL_PATTERN.sub("[EMAIL]", text)
    return _PHONE_PATTERN.sub("[PHONE]", without_email)


def create_safety_audit(
    text: str,
    safety_result: SafetyResult,
    ticket_id: str | None = None,
) -> SafetyAuditRecord:
    return SafetyAuditRecord(
        timestamp=datetime.now(UTC),
        ticket_id=ticket_id,
        anonymized_input=anonymize_input(text),
        trigger_reasons=safety_result.trigger_reasons,
        result="blocked" if safety_result.blocks_workflow else "allowed_with_controls",
        risk_level=safety_result.risk_level,
    )
