from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from pathlib import Path


def _jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def build_bundle(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "knowledge"
    bundle = tmp_path / "bundle"
    (root / "docs").mkdir(parents=True)
    (root / "transcripts").mkdir(parents=True)
    bundle.mkdir()
    files = {
        "docs/manual.pdf": b"approved source candidate",
        "transcripts/audio.txt": b"machine transcript",
    }
    for relative, content in files.items():
        (root / relative).write_bytes(content)

    cases = [
        {"case_id": "CASE-WA-010", "source_chat": "Restricted A", "knowledge_tier": "validated_case_library", "source_validation": "Bernardo Cerrai", "technical_access": "restricted", "domain": "legacy"},
        {"case_id": "CASE-WA-013", "source_chat": "Restricted B", "knowledge_tier": "validated_case_library", "source_validation": "Bernardo Cerrai", "technical_access": "restricted", "domain": "power"},
    ]
    attachments = [
        {"relative_path": relative, "file_name": Path(relative).name, "byte_size": len(content), "sha256": sha256(content).hexdigest(), "import_tier": "official_document" if relative.startswith("docs/") else "derived_transcript", "case_id": "" if relative.startswith("docs/") else "CASE-WA-010", "technical_access": "restricted", "source_format": Path(relative).suffix.lstrip("."), "hash_status": "verified"}
        for relative, content in files.items()
    ]
    documents = [{"document_id": "DOC-001", "knowledge_tier": "golden_technical_kb", "relative_path": "docs/manual.pdf", "filename": "manual.pdf", "mime_type": "application/pdf", "document_status": "candidate", "technical_access": "standard"}]
    scopes = [
        {"case_id": "CASE-WA-010", "model": "", "voltage_v": "", "serial_number": "", "hardware_revision": "", "software_revision": "", "match_status": "pending"},
        {"case_id": "CASE-WA-013", "model": "", "voltage_v": "", "serial_number": "", "hardware_revision": "", "software_revision": "", "match_status": "pending"},
    ]
    audio = [{"audio_id": "AUDIO-001", "case_id": "CASE-WA-010", "source_chat": "Restricted A", "language": "it", "original_opus": "raw/audio.opus", "converted_mp3": "derived/audio.mp3", "transcript": "transcripts/audio.txt", "transcript_status": "machine_transcript_unreviewed", "technical_use": "not_authoritative_pending_technical_review"}]
    _jsonl(bundle / "cases.jsonl", cases)
    _jsonl(bundle / "documents.jsonl", documents)
    _jsonl(bundle / "attachments.jsonl", attachments)
    _jsonl(bundle / "product_scopes.jsonl", scopes)
    _jsonl(bundle / "audio_transcripts.jsonl", audio)
    _jsonl(bundle / "duplicate_content_groups.jsonl", [])
    (bundle / "validation_report.json").write_text(json.dumps({"validation": {"import_ready": True}}), encoding="utf-8")
    return bundle, root
