"""Internal-only ticket API. It is not a public customer interface."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.services.ticket_service import (
    ProductUnitNotFoundError,
    SafetyPersistenceError,
    TicketNotFoundError,
    add_inbound_message,
    create_ticket,
    get_ticket,
    get_ticket_audit,
)


router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    include_in_schema=True,
)


class TicketCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=240)
    customer_id: UUID | None = None
    product_unit_id: UUID | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject: str
    status: str
    customer_id: UUID | None
    product_unit_id: UUID | None
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    text: str = Field(min_length=1)
    external_message_id: str = Field(min_length=1, max_length=240)


class MessageResultResponse(BaseModel):
    message_id: UUID
    duplicate: bool
    risk_level: str | None
    requires_human_review: bool
    workflow_blocked: bool
    customer_message_sent: bool


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID | None
    actor_type: str
    action: str
    status: str
    metadata_json: dict[str, Any]
    created_at: datetime


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Internal: create ticket",
)
async def create_internal_ticket(
    payload: TicketCreate,
    session: AsyncSession = Depends(get_db_session),
) -> TicketResponse:
    try:
        ticket = await create_ticket(session, **payload.model_dump())
    except ProductUnitNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Product unit not found") from exc
    return TicketResponse.model_validate(ticket)


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Internal: get ticket",
)
async def get_internal_ticket(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> TicketResponse:
    try:
        ticket = await get_ticket(session, ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found") from exc
    return TicketResponse.model_validate(ticket)


@router.post(
    "/tickets/{ticket_id}/messages",
    response_model=MessageResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Internal: persist inbound message and safety evaluation",
)
async def add_internal_ticket_message(
    ticket_id: UUID,
    payload: MessageCreate,
    session: AsyncSession = Depends(get_db_session),
) -> MessageResultResponse:
    try:
        result = await add_inbound_message(
            session,
            ticket_id,
            payload.text,
            payload.external_message_id,
        )
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found") from exc
    except SafetyPersistenceError as exc:
        raise HTTPException(status_code=503, detail="Safety persistence unavailable") from exc
    assessment = result.safety_assessment
    return MessageResultResponse(
        message_id=result.message.id,
        duplicate=result.duplicate,
        risk_level=assessment.risk_level if assessment else None,
        requires_human_review=assessment.requires_human_review if assessment else False,
        workflow_blocked=assessment.workflow_blocked if assessment else False,
        customer_message_sent=result.customer_message_sent,
    )


@router.get(
    "/tickets/{ticket_id}/audit",
    response_model=list[AuditEventResponse],
    summary="Internal: list immutable ticket audit events",
)
async def get_internal_ticket_audit(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[AuditEventResponse]:
    try:
        events = await get_ticket_audit(session, ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found") from exc
    return [AuditEventResponse.model_validate(event) for event in events]
