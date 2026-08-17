from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid
from pydantic import BaseModel

from app.database.session import get_db
from app.api.v1.deps import get_current_user, check_role
from app.services.curriculum_service import CurriculumService
from app.schemas.schemas import APIResponse, HeartbeatSchema, WeekResponse, ErrorResponseDetail
from app.models.models import User, ActivityEvent

router = APIRouter()

class OverrideLockRequest(BaseModel):
    student_id: uuid.UUID
    week_id: uuid.UUID

@router.get("/weeks", response_model=APIResponse[List[Any]])
async def get_weeks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve 12-week learning roadmap with completion states and locks."""
    weeks_data = await CurriculumService.get_weeks_for_student(db, current_user)
    return APIResponse(success=True, data=weeks_data)

@router.post("/content/heartbeat", response_model=APIResponse[Any])
async def track_heartbeat(
    body: HeartbeatSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Periodic client-side reading activity check-in to auto-complete modules."""
    result = await CurriculumService.track_content_heartbeat(db, current_user, body)
    return APIResponse(success=True, data=result, message="Heartbeat logged.")

@router.post("/admin/override-lock", response_model=APIResponse[bool])
async def override_lock(
    body: OverrideLockRequest,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Admin override to manually unlock a curriculum week for a student."""
    # Check if event already exists
    from sqlalchemy.future import select
    from app.models.models import Week
    
    week_result = await db.execute(select(Week).filter(Week.id == body.week_id))
    week = week_result.scalar_one_or_none()
    if not week:
        return APIResponse(
            success=False,
            data=False,
            error=ErrorResponseDetail(code="WEEK_NOT_FOUND", message="Week not found.")
        )
        
    override_event = ActivityEvent(
        user_id=body.student_id,
        event_type="ADMIN_OVERRIDE_UNLOCK_WEEK",
        entity_type="Week",
        entity_id=body.week_id,
        payload={"admin_id": str(current_user.id), "week_number": week.week_number}
    )
    db.add(override_event)
    await db.commit()
    
    return APIResponse(success=True, data=True, message=f"Week {week.week_number} successfully unlocked.")
