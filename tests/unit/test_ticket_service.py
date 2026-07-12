import pytest

from app.core.safety import RiskLevel, evaluate_safety
from app.services.ticket_service import ticket_status_for_safety


@pytest.mark.parametrize(
    ("text", "expected_status"),
    [
        ("Richiesta manutenzione", "open"),
        ("Il motore è surriscaldato", "requires_human_review"),
        ("Vedo fumo", "safety_blocked"),
    ],
)
def test_ticket_status_for_safety(text: str, expected_status: str) -> None:
    result = evaluate_safety(text)

    assert result.risk_level in RiskLevel
    assert ticket_status_for_safety(result) == expected_status
