import pytest

from app.core.safety import RiskLevel, SafetyCategory, evaluate_safety


@pytest.mark.parametrize(
    ("text", "category", "risk_level"),
    [
        ("Vedo fumo dalla macchina", SafetyCategory.SMOKE, RiskLevel.IMMEDIATE_STOP),
        ("Sento odore di bruciato", SafetyCategory.BURNING_ODOR, RiskLevel.IMMEDIATE_STOP),
        ("Escono scintille", SafetyCategory.SPARKS, RiskLevel.IMMEDIATE_STOP),
        ("Il cavo elettrico è danneggiato", SafetyCategory.DAMAGED_CABLES, RiskLevel.IMMEDIATE_STOP),
        ("Il compressore è surriscaldato", SafetyCategory.OVERHEATED_COMPONENTS, RiskLevel.WARNING),
        ("È entrata acqua sulla scheda", SafetyCategory.WATER_ON_ELECTRICAL_COMPONENTS, RiskLevel.IMMEDIATE_STOP),
        ("C'è rischio elettrico", SafetyCategory.ELECTRICAL_RISK, RiskLevel.IMMEDIATE_STOP),
        ("Potrebbe esserci una perdita di refrigerante", SafetyCategory.POSSIBLE_REFRIGERANT_LEAK, RiskLevel.WARNING),
        ("Vedo delle fiamme", SafetyCategory.FIRE_RISK, RiskLevel.IMMEDIATE_STOP),
    ],
)
def test_detects_safety_category(
    text: str,
    category: SafetyCategory,
    risk_level: RiskLevel,
) -> None:
    result = evaluate_safety(text)

    assert category in result.categories
    assert result.risk_level is risk_level
    assert result.requires_human_escalation is True
    assert result.blocks_workflow is (risk_level is RiskLevel.IMMEDIATE_STOP)


@pytest.mark.parametrize(
    "text",
    [
        "Non vedo fumo",
        "Non sento odore di bruciato",
        "Non ci sono scintille",
        "Nessun cavo danneggiato",
        "Il componente non è surriscaldato",
        "Non c'è acqua sulla scheda",
        "Non c'è rischio elettrico",
        "Non risulta perdita di refrigerante",
        "Nessun rischio di incendio",
    ],
)
def test_explicit_negation_does_not_trigger(text: str) -> None:
    result = evaluate_safety(text)

    assert result.risk_level is RiskLevel.NONE
    assert result.categories == ()


def test_critical_signal_has_priority_over_warning() -> None:
    result = evaluate_safety("Il compressore è surriscaldato e vedo fumo")

    assert result.risk_level is RiskLevel.IMMEDIATE_STOP
    assert result.blocks_workflow is True
