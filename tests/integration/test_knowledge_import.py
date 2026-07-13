from __future__ import annotations

from sqlalchemy import func, select

from app.models import AuditEvent
from app.models.knowledge import (
    KnowledgeAttachment,
    KnowledgeAudioTranscript,
    KnowledgeCase,
    KnowledgeContent,
    KnowledgeDocument,
    KnowledgeImportBatch,
)
from app.services.knowledge_import import KnowledgeImportService
from tests.knowledge_bundle_fixture import build_bundle


async def _count(session, model) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)))


async def test_transactional_import_preserves_governance(db_session, tmp_path):
    bundle, root = build_bundle(tmp_path)
    batch = await KnowledgeImportService(db_session).import_bundle(bundle, root, actor="test")
    assert batch.status == "completed"
    assert await _count(db_session, KnowledgeCase) == 2
    assert await _count(db_session, KnowledgeContent) == 2
    assert await _count(db_session, KnowledgeAttachment) == 2
    document = await db_session.scalar(select(KnowledgeDocument))
    transcript = await db_session.scalar(select(KnowledgeAudioTranscript))
    assert document is not None and document.authoritative is False
    assert transcript is not None and transcript.authoritative is False
    assert transcript.transcript_status == "machine_transcript_unreviewed"
    assert await db_session.scalar(select(AuditEvent).where(AuditEvent.action == "knowledge.import_completed"))


async def test_identical_import_is_idempotent(db_session, tmp_path):
    bundle, root = build_bundle(tmp_path)
    service = KnowledgeImportService(db_session)
    first = await service.import_bundle(bundle, root)
    first_counts = dict(first.counts)
    second = await service.import_bundle(bundle, root)
    assert second.id == first.id
    assert second.counts == first_counts
    assert await _count(db_session, KnowledgeImportBatch) == 1
    assert await _count(db_session, KnowledgeAttachment) == 2
