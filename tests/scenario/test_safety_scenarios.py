import pytest

from app.core.safety import RiskLevel, SafetyCategory
from app.services.safety_service import assess_message


@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("sento odore di bruciato", SafetyCategory.BURNING_ODOR),
        ("vedo fumo dalla macchina", SafetyCategory.SMOKE),
        ("è entrata acqua sulla scheda", SafetyCategory.WATER_ON_ELECTRICAL_COMPONENTS),
    ],
)
def test_critical_scenarios_stop_and_escalate(
    text: str,
    category: SafetyCategory,
) -> None:
    assessment = assess_message(text)

    assert assessment.safety_result.risk_level is RiskLevel.IMMEDIATE_STOP
    assert category in assessment.safety_result.categories
    assert assessment.safety_result.blocks_workflow is True
    assert assessment.safety_result.requires_human_escalation is True
    assert assessment.audit.result == "blocked"
    assert assessment.customer_message_sent is False


def test_ordinary_scenario_has_no_risk() -> None:
    assessment = assess_message("La macchina richiede la manutenzione annuale")

    assert assessment.safety_result.risk_level is RiskLevel.NONE
    assert assessment.safety_result.blocks_workflow is False
    assert assessment.customer_message_sent is False


def test_ambiguous_document_reference_does_not_trigger() -> None:
    assessment = assess_message("La parola fumo compare nel manuale")

    assert assessment.safety_result.risk_level is RiskLevel.NONE
    assert assessment.safety_result.categories == ()
    assert assessment.customer_message_sent is False
