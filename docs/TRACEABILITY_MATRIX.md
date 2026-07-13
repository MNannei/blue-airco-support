# Traceability Matrix

| ID | Requisito | Test | Stato |
|---|---|---|---|
| REQ-001 | Il servizio espone `GET /health` | `tests/unit/test_health.py::test_health` | Coperto |
| REQ-002 | Il progetto usa Python 3.12 | Vincolo `requires-python` in `pyproject.toml` | Configurato |
| REQ-003 | PostgreSQL è disponibile via Docker Compose e CI | Migrazione CI, `tests/integration` | Coperto |
| REQ-004 | Nessun invio automatico ai clienti | `tests/unit/test_safety_service.py`, `tests/scenario/test_safety_scenarios.py` | Coperto per il safety service |
| REQ-005 | Escalation umana obbligatoria per i rischi critici | `tests/unit/test_safety.py`, `tests/scenario/test_safety_scenarios.py` | Coperto |
| REQ-006 | Rilevamento deterministico delle nove categorie di rischio | `tests/unit/test_safety.py::test_detects_safety_category` | Coperto |
| REQ-007 | Negazioni e riferimenti documentali non generano falsi positivi noti | `tests/unit/test_safety.py::test_explicit_negation_does_not_trigger`, `tests/scenario/test_safety_scenarios.py::test_ambiguous_document_reference_does_not_trigger` | Coperto |
| REQ-008 | I casi critici bloccano il workflow ordinario | `tests/unit/test_safety_service.py::test_critical_message_blocks_workflow_and_creates_audit` | Coperto |
| REQ-009 | Ogni valutazione produce un audit strutturato e anonimizzato | `tests/unit/test_audit.py`, `tests/unit/test_safety_service.py` | Coperto |
| REQ-010 | SQLAlchemy asincrono usa DATABASE_URL e session factory | `tests/integration/test_ticket_persistence.py` | Coperto |
| REQ-011 | Lo schema è gestito da migrazioni ripetibili | `tests/integration/test_00_migrations.py` | Coperto |
| REQ-012 | Ticket, messaggio, safety assessment e audit sono persistiti | `tests/integration/test_ticket_persistence.py::test_ticket_message_safety_and_audit_are_persisted` | Coperto |
| REQ-013 | external_message_id impedisce duplicati anche concorrenti | test idempotenza in `tests/integration/test_ticket_persistence.py` | Coperto |
| REQ-014 | Un errore safety non elimina ticket e messaggio | `test_safety_persistence_error_preserves_ticket_and_message` | Coperto |
| REQ-015 | AuditEvent è immutabile a livello applicativo | `test_audit_event_is_immutable` | Coperto |
| REQ-016 | API ticket interne persistono safety e audit senza invio | `tests/integration/test_internal_ticket_api.py` | Coperto |
| REQ-017 | Il pacchetto knowledge viene validato prima della scrittura | `tests/unit/test_knowledge_import.py` | Coperto |
| REQ-018 | Hash errati e path traversal sono rifiutati | `tests/unit/test_knowledge_import.py` | Coperto |
| REQ-019 | L'import è transazionale, auditabile e idempotente | `tests/integration/test_knowledge_import.py` | Coperto |
| REQ-020 | Documenti non approvati e trascrizioni automatiche non sono autorevoli | `test_transactional_import_preserves_governance` | Coperto |
| REQ-021 | I casi riservati mantengono l'accesso ristretto | `test_restricted_access_cannot_be_removed` | Coperto |
