from __future__ import annotations

import json

import pytest

from app.services.knowledge_import import BundleValidationError, validate_bundle
from tests.knowledge_bundle_fixture import build_bundle


def test_complete_bundle_validates(tmp_path):
    bundle, root = build_bundle(tmp_path)
    result = validate_bundle(bundle, root)
    assert len(result.cases) == 2
    assert len(result.attachments) == 2
    assert result.audio_transcripts[0]["transcript_status"] == "machine_transcript_unreviewed"


def test_hash_mismatch_is_rejected(tmp_path):
    bundle, root = build_bundle(tmp_path)
    (root / "docs" / "manual.pdf").write_bytes(b"tampered")
    with pytest.raises(BundleValidationError, match="SHA-256 mismatch"):
        validate_bundle(bundle, root)


def test_path_traversal_is_rejected(tmp_path):
    bundle, root = build_bundle(tmp_path)
    rows = [json.loads(line) for line in (bundle / "attachments.jsonl").read_text().splitlines()]
    rows[0]["relative_path"] = "../outside.pdf"
    (bundle / "attachments.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(BundleValidationError, match="escapes knowledge root"):
        validate_bundle(bundle, root)


def test_restricted_access_cannot_be_removed(tmp_path):
    bundle, root = build_bundle(tmp_path)
    rows = [json.loads(line) for line in (bundle / "cases.jsonl").read_text().splitlines()]
    rows[0]["technical_access"] = "standard"
    (bundle / "cases.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(BundleValidationError, match="Restricted access lost"):
        validate_bundle(bundle, root)
