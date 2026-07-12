"""Minimal relational model for tickets, safety, audit, and webhook ingestion."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedModel


class User(TimestampedModel, Base):
    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(String(200), nullable=False)


class Customer(TimestampedModel, Base):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contacts: Mapped[list[Contact]] = relationship(back_populates="customer")
    vessels: Mapped[list[Vessel]] = relationship(back_populates="customer")


class Contact(TimestampedModel, Base):
    __tablename__ = "contacts"

    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[str] = mapped_column(String(320), nullable=False)
    customer: Mapped[Customer] = relationship(back_populates="contacts")


class Vessel(TimestampedModel, Base):
    __tablename__ = "vessels"

    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer: Mapped[Customer] = relationship(back_populates="vessels")
    product_units: Mapped[list[ProductUnit]] = relationship(back_populates="vessel")


class ProductUnit(TimestampedModel, Base):
    __tablename__ = "product_units"

    vessel_id: Mapped[UUID | None] = mapped_column(ForeignKey("vessels.id"))
    serial_number: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(200))
    vessel: Mapped[Vessel | None] = relationship(back_populates="product_units")
    tickets: Mapped[list[Ticket]] = relationship(back_populates="product_unit")


class Ticket(TimestampedModel, Base):
    __tablename__ = "tickets"

    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("customers.id"))
    product_unit_id: Mapped[UUID | None] = mapped_column(ForeignKey("product_units.id"))
    subject: Mapped[str] = mapped_column(String(240), nullable=False)
    product_unit: Mapped[ProductUnit | None] = relationship(back_populates="tickets")
    messages: Mapped[list[Message]] = relationship(back_populates="ticket")
    safety_assessments: Mapped[list[SafetyAssessment]] = relationship(back_populates="ticket")
    audit_events: Mapped[list[AuditEvent]] = relationship(back_populates="ticket")


class Message(TimestampedModel, Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("external_message_id", name="uq_messages_external_message_id"),)

    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    external_message_id: Mapped[str] = mapped_column(String(240), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default="inbound", nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ticket: Mapped[Ticket] = relationship(back_populates="messages")
    safety_assessments: Mapped[list[SafetyAssessment]] = relationship(back_populates="message")


class SafetyAssessment(TimestampedModel, Base):
    __tablename__ = "safety_assessments"

    ticket_id: Mapped[UUID | None] = mapped_column(ForeignKey("tickets.id"))
    message_id: Mapped[UUID | None] = mapped_column(ForeignKey("messages.id"))
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False)
    workflow_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    anonymized_input: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ticket: Mapped[Ticket | None] = relationship(back_populates="safety_assessments")
    message: Mapped[Message | None] = relationship(back_populates="safety_assessments")
    audit_events: Mapped[list[AuditEvent]] = relationship(back_populates="safety_assessment")


class AuditEvent(TimestampedModel, Base):
    __tablename__ = "audit_events"

    ticket_id: Mapped[UUID | None] = mapped_column(ForeignKey("tickets.id"))
    safety_assessment_id: Mapped[UUID | None] = mapped_column(ForeignKey("safety_assessments.id"))
    actor_type: Mapped[str] = mapped_column(String(40), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    ticket: Mapped[Ticket | None] = relationship(back_populates="audit_events")
    safety_assessment: Mapped[SafetyAssessment | None] = relationship(back_populates="audit_events")


class WebhookEvent(TimestampedModel, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("external_message_id", name="uq_webhook_external_message_id"),)

    external_message_id: Mapped[str] = mapped_column(String(240), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


def _reject_audit_mutation(*_: object, **__: object) -> None:
    raise ValueError("AuditEvent records are immutable")


event.listen(AuditEvent, "before_update", _reject_audit_mutation)
event.listen(AuditEvent, "before_delete", _reject_audit_mutation)
