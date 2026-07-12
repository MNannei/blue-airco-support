"""Deterministic safety checks independent from generative models."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    NONE = "none"
    WARNING = "warning"
    IMMEDIATE_STOP = "immediate_stop"


class SafetyCategory(str, Enum):
    SMOKE = "smoke"
    BURNING_ODOR = "burning_odor"
    SPARKS = "sparks"
    DAMAGED_CABLES = "damaged_cables"
    OVERHEATED_COMPONENTS = "overheated_components"
    WATER_ON_ELECTRICAL_COMPONENTS = "water_on_electrical_components"
    ELECTRICAL_RISK = "electrical_risk"
    POSSIBLE_REFRIGERANT_LEAK = "possible_refrigerant_leak"
    FIRE_RISK = "fire_risk"


@dataclass(frozen=True)
class SafetyResult:
    risk_level: RiskLevel
    categories: tuple[SafetyCategory, ...]
    trigger_reasons: tuple[str, ...]
    conservative_message: str
    requires_human_escalation: bool
    blocks_workflow: bool


@dataclass(frozen=True)
class _Rule:
    category: SafetyCategory
    risk_level: RiskLevel
    pattern: re.Pattern[str]
    reason: str


_RULES = (
    _Rule(SafetyCategory.SMOKE, RiskLevel.IMMEDIATE_STOP, re.compile(r"\bfumo\b"), "Presenza dichiarata di fumo."),
    _Rule(SafetyCategory.BURNING_ODOR, RiskLevel.IMMEDIATE_STOP, re.compile(r"\b(?:odore|puzza)\s+di\s+bruciat[oa]\b"), "Odore di bruciato dichiarato."),
    _Rule(SafetyCategory.SPARKS, RiskLevel.IMMEDIATE_STOP, re.compile(r"\bscintill(?:a|e|io)\b"), "Presenza dichiarata di scintille."),
    _Rule(SafetyCategory.DAMAGED_CABLES, RiskLevel.IMMEDIATE_STOP, re.compile(r"\bcav[oi]\s+(?:elettric[oi]\s+)?(?:(?:e|è|risulta)\s+)?(?:danneggiat[oi]|spellat[oi]|rovinat[oi])\b"), "Cavi danneggiati dichiarati."),
    _Rule(SafetyCategory.OVERHEATED_COMPONENTS, RiskLevel.WARNING, re.compile(r"\b(?:componente|scheda|motore|compressore)\s+(?:(?:e|è|risulta)\s+)?(?:molto\s+)?(?:surriscaldat[oa]|bollente)\b"), "Possibile surriscaldamento dichiarato."),
    _Rule(SafetyCategory.WATER_ON_ELECTRICAL_COMPONENTS, RiskLevel.IMMEDIATE_STOP, re.compile(r"\bacqua\b.{0,40}\b(?:scheda|quadro\s+elettrico|component[ei]\s+elettric[oi])\b"), "Acqua su componenti elettrici dichiarata."),
    _Rule(SafetyCategory.ELECTRICAL_RISK, RiskLevel.IMMEDIATE_STOP, re.compile(r"\b(?:rischio\s+elettrico|scossa\s+elettrica|prendo\s+la\s+scossa|dispersione\s+elettrica)\b"), "Rischio elettrico dichiarato."),
    _Rule(SafetyCategory.POSSIBLE_REFRIGERANT_LEAK, RiskLevel.WARNING, re.compile(r"\b(?:perdita|fuoriuscita)\s+(?:di\s+)?(?:gas|refrigerante)\b"), "Possibile perdita di refrigerante dichiarata; causa non verificata."),
    _Rule(SafetyCategory.FIRE_RISK, RiskLevel.IMMEDIATE_STOP, re.compile(r"\b(?:rischio\s+(?:di\s+)?incendio|principio\s+d['’]incendio|fiamm[ae])\b"), "Possibile rischio incendio dichiarato."),
)

_NON_OPERATIONAL_CONTEXTS = (
    re.compile(r"\bnel\s+manuale\b"),
    re.compile(r"\bcome\s+esempio\b"),
    re.compile(r"\bsimulazione\b"),
    re.compile(r"\bscenario\s+ipotetico\b"),
)

_NEGATION_BEFORE_TRIGGER = re.compile(
    r"(?:non\s+(?:c['’]?[eè]|vedo|sento|ci\s+sono|risulta|presenta|segnalo)?|"
    r"nessun[oa]?|senza)\s*$"
)

_RISK_PRIORITY = {
    RiskLevel.NONE: 0,
    RiskLevel.WARNING: 1,
    RiskLevel.IMMEDIATE_STOP: 2,
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def _is_negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 45) : start]
    return _NEGATION_BEFORE_TRIGGER.search(prefix) is not None


def evaluate_safety(text: str) -> SafetyResult:
    """Evaluate explicit safety signals without inferring a technical cause."""
    normalized = _normalize(text)
    if not normalized or any(pattern.search(normalized) for pattern in _NON_OPERATIONAL_CONTEXTS):
        return _no_risk_result()

    matches: list[_Rule] = []
    for rule in _RULES:
        match = rule.pattern.search(normalized)
        if match is not None and not _is_negated(normalized, match.start()):
            matches.append(rule)

    if not matches:
        return _no_risk_result()

    risk_level = max(matches, key=lambda item: _RISK_PRIORITY[item.risk_level]).risk_level
    blocks_workflow = risk_level is RiskLevel.IMMEDIATE_STOP
    if blocks_workflow:
        message = (
            "Interrompere il workflow ordinario e non procedere con azioni tecniche. "
            "Richiedere immediatamente la valutazione di un tecnico qualificato; "
            "la causa non è stata determinata."
        )
    else:
        message = (
            "Non assumere una causa tecnica. Sospendere la preparazione della bozza e "
            "richiedere una revisione umana prima di proseguire."
        )

    return SafetyResult(
        risk_level=risk_level,
        categories=tuple(rule.category for rule in matches),
        trigger_reasons=tuple(rule.reason for rule in matches),
        conservative_message=message,
        requires_human_escalation=True,
        blocks_workflow=blocks_workflow,
    )


def _no_risk_result() -> SafetyResult:
    return SafetyResult(
        risk_level=RiskLevel.NONE,
        categories=(),
        trigger_reasons=(),
        conservative_message="Nessun segnale di rischio esplicito rilevato.",
        requires_human_escalation=False,
        blocks_workflow=False,
    )
