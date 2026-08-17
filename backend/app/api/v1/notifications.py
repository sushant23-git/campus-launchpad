from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid

from app.database.session import get_db
from app.api.v1.deps import get_current_user
from app.services.notification_service import NotificationService
from app.schemas.schemas import APIResponse, NotificationResponse
from app.models.models import User

router = APIRouter()

@router.get("", response_model=APIResponse[List[NotificationResponse]])
async def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve all notifications queued for the current student."""
    notes = await NotificationService.get_my_notifications(db, current_user.id)
    resp = [NotificationResponse.from_orm(n) for n in notes]
    return APIResponse(success=True, data=resp)

@router.post("/{notification_id}/read", response_model=APIResponse[NotificationResponse])
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Mark a queued notification as read, removing active notification badge."""
    note = await NotificationService.mark_notification_as_read(db, current_user.id, notification_id)
    resp = NotificationResponse.from_orm(note)
    return APIResponse(success=True, data=resp, message="Notification marked as read.")
