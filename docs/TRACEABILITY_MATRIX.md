# Traceability Matrix

| ID | Requisito | Test | Stato |
|---|---|---|---|
| REQ-001 | Il servizio espone `GET /health` | `tests/unit/test_health.py::test_health` | Coperto |
| REQ-002 | Il progetto usa Python 3.12 | Vincolo `requires-python` in `pyproject.toml` | Configurato |
| REQ-003 | PostgreSQL è disponibile via Docker Compose | Test di integrazione da definire | Non coperto |
| REQ-004 | Nessun invio automatico ai clienti | Scenario test da definire | Non implementato |
| REQ-005 | Approvazione umana obbligatoria per le bozze | Scenario test da definire | Non implementato |

