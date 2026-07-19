# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose and scope boundaries

Blue Airco Support is an internal copilot for Blue Airco technicians (Italian manufacturer of DC electronic systems: battery chargers, inverters, converters). It currently exposes only a FastAPI service backed by PostgreSQL. Explicitly out of scope right now — do not add or wire up:

- Outbound customer messaging of any kind (WhatsApp, email, etc.)
- Automatic/unattended responses to customers
- OpenAI or any LLM integration
- Automated technical diagnoses or unapproved operational actions

Every draft response is meant for human review; nothing sends to a customer automatically. See `docs/PRODUCT_SPEC.md` and `AGENTS.md` for the binding rules — notably: never fabricate diagnoses, technical data, or machine identifiers; never suppress or mutate audit records; treat all external input as untrusted; get explicit human approval before irreversible/high-impact actions.

## Commands

Environment setup (Python 3.12 required, matches `requires-python = ">=3.12,<3.13"`):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Database (PostgreSQL via Docker Compose; app never calls `create_all`, schema is Alembic-only):

```bash
docker compose up -d db
python -m alembic upgrade head        # apply schema
python -m alembic downgrade base      # revert
```

Run the API:

```bash
python -m uvicorn app.main:app --reload   # http://localhost:8000, health at GET /health
```

Tests (pytest-asyncio in `auto` mode; integration/scenario tests need a live, migrated PostgreSQL):

```bash
python -m pytest                                  # full suite
python -m pytest tests/unit                        # unit only, no DB required
python -m pytest tests/integration tests/scenario   # DB-backed tests
python -m pytest tests/unit/test_safety.py::test_name -vv   # single test
```

CI (`.github/workflows/ci.yml`) spins up real Postgres, installs `.[dev]`, verifies the app imports, runs `alembic upgrade head`, then runs unit tests followed by integration+scenario tests as separate steps.

Knowledge base import CLI (installed as `knowledge-import` console script, `app/cli/knowledge_import.py`):

```bash
knowledge-import validate <bundle-path> --knowledge-root <knowledge-root>
knowledge-import run <bundle-path> --knowledge-root <knowledge-root> [--actor <name>]
knowledge-import report <batch-key>
```

Raw customer data must never be added to this repository. The knowledge bundle source files live outside the repo; only governed metadata/hashes are persisted to Postgres.

## Architecture

Layering: `api` (FastAPI routers) → `services` (transactional use cases) → `models` (SQLAlchemy ORM entities) → Postgres, with `core` holding LLM-independent domain logic that other layers depend on but that has no framework dependencies itself.

- `app/config.py` — `pydantic-settings` `Settings`, loaded from `.env` / env vars (`DATABASE_URL`, `APP_NAME`, `APP_ENV`).
- `app/database.py` — async SQLAlchemy engine/session factory; `get_db_session` is the FastAPI dependency. Sessions do not own transaction boundaries — services call `commit`/`rollback`/`refresh` explicitly.
- `app/core/safety.py` — deterministic, regex-based safety engine (`evaluate_safety`), completely independent of any LLM. Classifies free text into `RiskLevel.NONE / WARNING / IMMEDIATE_STOP` across categories like smoke, sparks, damaged cables, electrical risk. Uses negation detection (`_is_negated`) and non-operational-context filters (manual examples, simulations) to avoid false positives. `IMMEDIATE_STOP` sets `blocks_workflow=True`; both `WARNING` and `IMMEDIATE_STOP` set `requires_human_escalation=True`. This module never infers a technical cause — only flags explicit signals.
- `app/core/audit.py` — `anonymize_input` strips emails/phone numbers before anything is persisted or logged; `create_safety_audit` builds an in-memory audit record from a `SafetyResult`.
- `app/models/entities.py` — core domain: `User`, `Customer`, `Contact`, `Vessel`, `ProductUnit`, `Ticket`, `Message`, `SafetyAssessment`, `AuditEvent`, `WebhookEvent`. All inherit `TimestampedModel` (`id: UUID`, `created_at`, `updated_at`, `status`) from `app/models/base.py`. `AuditEvent` rows are made immutable at the ORM level via `before_update`/`before_delete` event listeners that raise — audit trails cannot be edited or deleted through the ORM, and this must not be worked around.
- `app/models/knowledge.py` — governed knowledge base metadata: `KnowledgeImportBatch`, `KnowledgeCase`, `KnowledgeContent` (dedup by `sha256`), `KnowledgeAttachment`, `KnowledgeDocument`, `KnowledgeProductScope`, `KnowledgeAudioTranscript`. Only `document_status == "approved"` documents may have `authoritative=True`; machine transcripts are always imported non-authoritative.
- `app/services/ticket_service.py` — the main transactional workflow. `add_inbound_message` dedupes on `Message.external_message_id` (checked in-app and enforced by a unique DB constraint for concurrent retries — duplicates are recorded as an `AuditEvent`, not rejected as errors), then calls `persist_safety_evaluation`, which runs `evaluate_safety`, persists a `SafetyAssessment` + `AuditEvent` in the same transaction, and updates `Ticket.status` via `ticket_status_for_safety` (`safety_blocked` / `requires_human_review` / `open`). If safety persistence fails after the message is already committed, the ticket is preserved and marked `safety_persistence_error` (never silently dropped) and `SafetyPersistenceError` is raised.
- `app/services/knowledge_import.py` + `app/cli/knowledge_import.py` — validates a knowledge bundle (SHA-256 hashes, path traversal checks, case associations, governance status) and imports it transactionally with content-level deduplication; exposed only via the local `knowledge-import` CLI, not HTTP.
- `app/api/internal_tickets.py` — `/internal/*` routes (create ticket, get ticket, post message, get audit trail). These are **internal tooling endpoints with no authentication** — never expose them publicly or treat them as a customer-facing API.
- `alembic/` — versioned schema (`versions/0001_initial_schema.py`, `0002_knowledge_import.py`). The app never runs `Base.metadata.create_all`; all schema changes go through a new Alembic revision.

Expected end-to-end flow (not fully implemented yet, but the shape future work should follow): `messaggio → safety engine → identificazione macchina → workflow → fonti approvate → bozza → approvazione umana`. Drafts are never auto-sent; there is no diagnosis certainty implied anywhere in this pipeline.

## Conventions worth knowing

- Domain/user-facing strings (safety rules, docs, commit-adjacent prose in this repo) are in Italian; code identifiers and comments are in English.
- New safety rules or negative test cases must not weaken existing critical (`IMMEDIATE_STOP`) detections — `docs/TEST_STRATEGY.md` requires a documented case and a regression test for any new exclusion.
- `tests/conftest.py`'s `db_session` fixture truncates all tables (including knowledge tables) before each test that uses it — integration/scenario tests assume a clean, migrated database per run.
- Test suite is organized by kind under `tests/`: `unit` (no DB), `integration`, `scenario`, `end_to_end` — mirrors the test taxonomy defined in `docs/TEST_STRATEGY.md`.
