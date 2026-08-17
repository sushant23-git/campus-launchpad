import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.models.models import Notification
from app.core.exceptions import NotFoundException

class NotificationService:
    @staticmethod
    async def get_my_notifications(db: AsyncSession, user_id: uuid.UUID) -> List[Notification]:
        """Fetch all notifications for the logged in user, sorted by descending date."""
        result = await db.execute(
            select(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def mark_notification_as_read(
        db: AsyncSession,
        user_id: uuid.UUID,
        notification_id: uuid.UUID
    ) -> Notification:
        """Mark a specific notification as read, checking ownership rules."""
        result = await db.execute(
            select(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise NotFoundException("Notification not found.")

        notification.is_read = True
        await db.commit()
        return notification

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str, # Info, Deadline, Alert, Grade
        reference_entity_type: Optional[str] = None,
        reference_entity_id: Optional[uuid.UUID] = None
    ) -> Notification:
        """Create and queue a new notification for a specific user."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False,
            reference_entity_type=reference_entity_type,
            reference_entity_id=reference_entity_id,
            created_at=datetime.utcnow()
        )
        db.add(notification)
        await db.flush()
        return notification
