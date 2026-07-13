"""Internal CLI for validation and import of governed knowledge bundles."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.database import AsyncSessionFactory
from app.models.knowledge import KnowledgeImportBatch
from app.services.knowledge_import import KnowledgeImportService, validate_bundle


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knowledge-import")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        command = sub.add_parser(name)
        command.add_argument("bundle_path", type=Path)
        command.add_argument("--knowledge-root", type=Path, required=True)
    run = sub.choices["run"]
    run.add_argument("--actor", default="knowledge-import-cli")
    report = sub.add_parser("report")
    report.add_argument("batch_key")
    return parser


async def _run(args: argparse.Namespace) -> int:
    if args.command == "validate":
        bundle = validate_bundle(args.bundle_path, args.knowledge_root)
        print(json.dumps({"valid": True, "batch_key": bundle.batch_key, "attachments": len(bundle.attachments)}))
        return 0
    async with AsyncSessionFactory() as session:
        if args.command == "run":
            batch = await KnowledgeImportService(session).import_bundle(
                args.bundle_path, args.knowledge_root, actor=args.actor
            )
            print(json.dumps({"batch_key": batch.batch_key, "status": batch.status, "counts": batch.counts}))
            return 0
        batch = await session.scalar(
            select(KnowledgeImportBatch).where(KnowledgeImportBatch.batch_key == args.batch_key)
        )
        if batch is None:
            print(json.dumps({"error": "batch_not_found"}))
            return 1
        print(json.dumps({"batch_key": batch.batch_key, "status": batch.status, "counts": batch.counts, "errors": batch.errors}))
        return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run(_parser().parse_args())))


if __name__ == "__main__":
    main()
