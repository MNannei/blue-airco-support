# Traceability Matrix

| ID | Requisito | Test | Stato |
|---|---|---|---|
| REQ-001 | Il servizio espone `GET /health` | `tests/unit/test_health.py::test_health` | Coperto |
| REQ-002 | Il progetto usa Python 3.12 | Vincolo `requires-python` in `pyproject.toml` | Configurato |
| REQ-003 | PostgreSQL è disponibile via Docker Compose | Test di integrazione da definire | Non coperto |
| REQ-004 | Nessun invio automatico ai clienti | `tests/unit/test_safety_service.py`, `tests/scenario/test_safety_scenarios.py` | Coperto per il safety service |
| REQ-005 | Escalation umana obbligatoria per i rischi critici | `tests/unit/test_safety.py`, `tests/scenario/test_safety_scenarios.py` | Coperto |
| REQ-006 | Rilevamento deterministico delle nove categorie di rischio | `tests/unit/test_safety.py::test_detects_safety_category` | Coperto |
| REQ-007 | Negazioni e riferimenti documentali non generano falsi positivi noti | `tests/unit/test_safety.py::test_explicit_negation_does_not_trigger`, `tests/scenario/test_safety_scenarios.py::test_ambiguous_document_reference_does_not_trigger` | Coperto |
| REQ-008 | I casi critici bloccano il workflow ordinario | `tests/unit/test_safety_service.py::test_critical_message_blocks_workflow_and_creates_audit` | Coperto |
| REQ-009 | Ogni valutazione produce un audit strutturato e anonimizzato | `tests/unit/test_audit.py`, `tests/unit/test_safety_service.py` | Coperto |
