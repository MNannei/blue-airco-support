"""Deterministic, audited import of governed Blue Airco knowledge packages."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent
from app.models.knowledge import (
    KnowledgeAttachment,
    KnowledgeAudioTranscript,
    KnowledgeCase,
    KnowledgeContent,
    KnowledgeDocument,
    KnowledgeImportBatch,
    KnowledgeProductScope,
)


REQUIRED_FILES = (
    "cases.jsonl",
    "documents.jsonl",
    "attachments.jsonl",
    "product_scopes.jsonl",
    "audio_transcripts.jsonl",
    "duplicate_content_groups.jsonl",
    "validation_report.json",
)
RESTRICTED_CASES = {"CASE-WA-010", "CASE-WA-013"}


class BundleValidationError(ValueError):
    """Raised when the package cannot be safely imported."""


@dataclass(frozen=True)
class ValidatedBundle:
    bundle_path: Path
    knowledge_root: Path
    batch_key: str
    cases: list[dict[str, Any]]
    documents: list[dict[str, Any]]
    attachments: list[dict[str, Any]]
    product_scopes: list[dict[str, Any]]
    audio_transcripts: list[dict[str, Any]]
    duplicate_groups: list[dict[str, Any]]
    report: dict[str, Any]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BundleValidationError(f"Invalid JSON in {path.name}:{line_number}") from exc
        if not isinstance(value, dict):
            raise BundleValidationError(f"Expected object in {path.name}:{line_number}")
        rows.append(value)
    return rows


def _unique(rows: list[dict[str, Any]], key: str, file_name: str) -> None:
    values = [str(row.get(key, "")) for row in rows]
    if any(not value for value in values):
        raise BundleValidationError(f"Missing {key} in {file_name}")
    if len(values) != len(set(values)):
        raise BundleValidationError(f"Duplicate {key} in {file_name}")


def _safe_source_path(root: Path, relative_path: str) -> Path:
    if not relative_path or Path(relative_path).is_absolute():
        raise BundleValidationError(f"Unsafe absolute or empty path: {relative_path!r}")
    candidate = (root / Path(*relative_path.split("/"))).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise BundleValidationError(f"Path escapes knowledge root: {relative_path}") from exc
    return candidate


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_bundle(bundle_path: Path, knowledge_root: Path) -> ValidatedBundle:
    bundle = bundle_path.resolve()
    root = knowledge_root.resolve()
    missing = [name for name in REQUIRED_FILES if not (bundle / name).is_file()]
    if missing:
        raise BundleValidationError(f"Missing bundle files: {', '.join(missing)}")

    report = json.loads((bundle / "validation_report.json").read_text(encoding="utf-8-sig"))
    if report.get("validation", {}).get("import_ready") is not True:
        raise BundleValidationError("Source validation report is not import-ready")

    cases = _read_jsonl(bundle / "cases.jsonl")
    documents = _read_jsonl(bundle / "documents.jsonl")
    attachments = _read_jsonl(bundle / "attachments.jsonl")
    scopes = _read_jsonl(bundle / "product_scopes.jsonl")
    audio = _read_jsonl(bundle / "audio_transcripts.jsonl")
    duplicates = _read_jsonl(bundle / "duplicate_content_groups.jsonl")

    _unique(cases, "case_id", "cases.jsonl")
    _unique(documents, "document_id", "documents.jsonl")
    _unique(attachments, "relative_path", "attachments.jsonl")
    _unique(scopes, "case_id", "product_scopes.jsonl")
    _unique(audio, "audio_id", "audio_transcripts.jsonl")

    case_by_id = {row["case_id"]: row for row in cases}
    if not RESTRICTED_CASES.issubset(case_by_id):
        raise BundleValidationError("Required restricted cases are missing")
    for case_id in RESTRICTED_CASES:
        if case_by_id[case_id].get("technical_access") != "restricted":
            raise BundleValidationError(f"Restricted access lost for {case_id}")

    attachment_by_path: dict[str, dict[str, Any]] = {}
    for row in attachments:
        relative = str(row["relative_path"])
        source = _safe_source_path(root, relative)
        if not source.is_file():
            raise BundleValidationError(f"Missing attachment: {relative}")
        expected = str(row.get("sha256", "")).lower()
        if len(expected) != 64 or _file_sha256(source) != expected:
            raise BundleValidationError(f"SHA-256 mismatch: {relative}")
        case_id = str(row.get("case_id", ""))
        if case_id and case_id not in case_by_id:
            raise BundleValidationError(f"Unknown attachment case: {case_id}")
        attachment_by_path[relative] = row

    for row in documents:
        if row.get("relative_path") not in attachment_by_path:
            raise BundleValidationError(f"Document attachment missing: {row.get('relative_path')}")
    for row in scopes:
        if row.get("case_id") not in case_by_id:
            raise BundleValidationError(f"Unknown product-scope case: {row.get('case_id')}")
    for row in audio:
        if row.get("case_id") not in case_by_id:
            raise BundleValidationError(f"Unknown audio case: {row.get('case_id')}")
        if row.get("transcript") not in attachment_by_path:
            raise BundleValidationError(f"Transcript attachment missing: {row.get('transcript')}")
        if row.get("transcript_status") != "machine_transcript_unreviewed":
            raise BundleValidationError("Unexpected transcript approval state")

    digest = sha256()
    for name in REQUIRED_FILES:
        digest.update(name.encode())
        digest.update((bundle / name).read_bytes())
    return ValidatedBundle(
        bundle, root, digest.hexdigest(), cases, documents, attachments, scopes, audio,
        duplicates, report,
    )


def _clean(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _changed(instance: Any, values: dict[str, Any]) -> bool:
    changed = False
    for field, value in values.items():
        if getattr(instance, field) != value:
            setattr(instance, field, value)
            changed = True
    return changed


class KnowledgeImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def import_bundle(
        self, bundle_path: Path, knowledge_root: Path, *, actor: str = "codex_import"
    ) -> KnowledgeImportBatch:
        validated = validate_bundle(bundle_path, knowledge_root)
        counts = {"inserted": 0, "updated": 0, "skipped": 0}
        async with self.session.begin():
            existing_batch = await self.session.scalar(
                select(KnowledgeImportBatch).where(
                    KnowledgeImportBatch.batch_key == validated.batch_key
                )
            )
            if existing_batch is not None and existing_batch.status == "completed":
                return existing_batch
            batch = existing_batch or KnowledgeImportBatch(
                batch_key=validated.batch_key,
                source_path=str(validated.bundle_path),
                actor=actor,
                status="running",
                counts={},
                errors=[],
            )
            if existing_batch is None:
                self.session.add(batch)

            cases: dict[str, KnowledgeCase] = {}
            for row in validated.cases:
                key = row["case_id"]
                record = await self.session.scalar(
                    select(KnowledgeCase).where(KnowledgeCase.external_case_id == key)
                )
                values = {
                    "source_chat": row["source_chat"],
                    "knowledge_tier": row["knowledge_tier"],
                    "source_validation": row["source_validation"],
                    "technical_access": row["technical_access"],
                    "domain": row["domain"],
                    "payload": row,
                    "status": "active",
                }
                if record is None:
                    record = KnowledgeCase(external_case_id=key, **values)
                    self.session.add(record)
                    counts["inserted"] += 1
                elif _changed(record, values):
                    counts["updated"] += 1
                else:
                    counts["skipped"] += 1
                cases[key] = record
            await self.session.flush()

            contents: dict[str, KnowledgeContent] = {}
            attachment_by_path: dict[str, KnowledgeAttachment] = {}
            for row in validated.attachments:
                digest = row["sha256"]
                content = contents.get(digest) or await self.session.scalar(
                    select(KnowledgeContent).where(KnowledgeContent.sha256 == digest)
                )
                if content is None:
                    content = KnowledgeContent(
                        sha256=digest,
                        byte_size=int(row["byte_size"]),
                        canonical_path=row["relative_path"],
                        source_format=row["source_format"],
                    )
                    self.session.add(content)
                    await self.session.flush()
                    counts["inserted"] += 1
                contents[digest] = content

                path = row["relative_path"]
                attachment = await self.session.scalar(
                    select(KnowledgeAttachment).where(KnowledgeAttachment.relative_path == path)
                )
                values = {
                    "content_id": content.id,
                    "case_id": cases[row["case_id"]].id if row.get("case_id") else None,
                    "import_tier": row["import_tier"],
                    "technical_access": row["technical_access"],
                    "source_format": row["source_format"],
                    "status": "active",
                }
                if attachment is None:
                    attachment = KnowledgeAttachment(relative_path=path, **values)
                    self.session.add(attachment)
                    counts["inserted"] += 1
                elif _changed(attachment, values):
                    counts["updated"] += 1
                else:
                    counts["skipped"] += 1
                attachment_by_path[path] = attachment
            await self.session.flush()

            for row in validated.documents:
                key = row["document_id"]
                attachment = attachment_by_path[row["relative_path"]]
                record = await self.session.scalar(
                    select(KnowledgeDocument).where(KnowledgeDocument.external_document_id == key)
                )
                values = {
                    "content_id": attachment.content_id,
                    "relative_path": row["relative_path"],
                    "title": row["filename"],
                    "knowledge_tier": row["knowledge_tier"],
                    "document_status": row["document_status"],
                    "technical_access": row["technical_access"],
                    "authoritative": row["document_status"] == "approved",
                    "payload": row,
                    "status": "active",
                }
                if record is None:
                    self.session.add(KnowledgeDocument(external_document_id=key, **values))
                    counts["inserted"] += 1
                elif _changed(record, values):
                    counts["updated"] += 1
                else:
                    counts["skipped"] += 1

            for row in validated.product_scopes:
                case = cases[row["case_id"]]
                record = await self.session.scalar(
                    select(KnowledgeProductScope).where(KnowledgeProductScope.case_id == case.id)
                )
                values = {
                    "model_name": _clean(row.get("model")),
                    "voltage_v": _clean(row.get("voltage_v")),
                    "serial_number": _clean(row.get("serial_number")),
                    "hardware_revision": _clean(row.get("hardware_revision")),
                    "software_revision": _clean(row.get("software_revision")),
                    "match_status": row["match_status"],
                    "payload": row,
                    "status": "active",
                }
                if record is None:
                    self.session.add(KnowledgeProductScope(case_id=case.id, **values))
                    counts["inserted"] += 1
                elif _changed(record, values):
                    counts["updated"] += 1
                else:
                    counts["skipped"] += 1

            for row in validated.audio_transcripts:
                key = row["audio_id"]
                record = await self.session.scalar(
                    select(KnowledgeAudioTranscript).where(KnowledgeAudioTranscript.audio_id == key)
                )
                values = {
                    "case_id": cases[row["case_id"]].id,
                    "transcript_path": row["transcript"],
                    "language": row["language"],
                    "transcript_status": "machine_transcript_unreviewed",
                    "authoritative": False,
                    "payload": row,
                    "status": "active",
                }
                if record is None:
                    self.session.add(KnowledgeAudioTranscript(audio_id=key, **values))
                    counts["inserted"] += 1
                elif _changed(record, values):
                    counts["updated"] += 1
                else:
                    counts["skipped"] += 1

            batch.status = "completed"
            batch.counts = counts
            self.session.add(
                AuditEvent(
                    actor_type="system",
                    action="knowledge.import_completed",
                    metadata_json={"batch_key": batch.batch_key, "actor": actor, **counts},
                )
            )
        return batch
