"""Governed technical knowledge and deterministic import records."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedModel


class KnowledgeImportBatch(TimestampedModel, Base):
    __tablename__ = "knowledge_import_batches"

    batch_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    counts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)


class KnowledgeCase(TimestampedModel, Base):
    __tablename__ = "knowledge_cases"

    external_case_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    source_chat: Mapped[str] = mapped_column(String(240), nullable=False)
    knowledge_tier: Mapped[str] = mapped_column(String(80), nullable=False)
    source_validation: Mapped[str] = mapped_column(String(160), nullable=False)
    technical_access: Mapped[str] = mapped_column(String(40), nullable=False)
    domain: Mapped[str] = mapped_column(String(160), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class KnowledgeContent(TimestampedModel, Base):
    __tablename__ = "knowledge_contents"

    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    byte_size: Mapped[int] = mapped_column(nullable=False)
    canonical_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_format: Mapped[str] = mapped_column(String(40), nullable=False)
    attachments: Mapped[list[KnowledgeAttachment]] = relationship(back_populates="content")


class KnowledgeAttachment(TimestampedModel, Base):
    __tablename__ = "knowledge_attachments"
    __table_args__ = (UniqueConstraint("relative_path", name="uq_knowledge_attachment_path"),)

    content_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_contents.id"), nullable=False)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("knowledge_cases.id"))
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    import_tier: Mapped[str] = mapped_column(String(80), nullable=False)
    technical_access: Mapped[str] = mapped_column(String(40), nullable=False)
    source_format: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[KnowledgeContent] = relationship(back_populates="attachments")


class KnowledgeDocument(TimestampedModel, Base):
    __tablename__ = "knowledge_documents"

    external_document_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    content_id: Mapped[UUID | None] = mapped_column(ForeignKey("knowledge_contents.id"))
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    knowledge_tier: Mapped[str] = mapped_column(String(80), nullable=False)
    document_status: Mapped[str] = mapped_column(String(40), nullable=False)
    technical_access: Mapped[str] = mapped_column(String(40), nullable=False)
    authoritative: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class KnowledgeProductScope(TimestampedModel, Base):
    __tablename__ = "knowledge_product_scopes"

    case_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_cases.id"), unique=True, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(200))
    voltage_v: Mapped[str | None] = mapped_column(String(40))
    serial_number: Mapped[str | None] = mapped_column(String(120))
    hardware_revision: Mapped[str | None] = mapped_column(String(120))
    software_revision: Mapped[str | None] = mapped_column(String(120))
    match_status: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class KnowledgeAudioTranscript(TimestampedModel, Base):
    __tablename__ = "knowledge_audio_transcripts"

    audio_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_cases.id"), nullable=False)
    transcript_path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    transcript_status: Mapped[str] = mapped_column(String(60), nullable=False)
    authoritative: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
