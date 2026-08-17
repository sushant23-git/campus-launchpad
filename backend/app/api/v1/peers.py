from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Optional
import uuid
from pydantic import BaseModel

from app.database.session import get_db
from app.api.v1.deps import get_current_user, check_role
from app.services.peer_service import PeerService
from app.schemas.schemas import (
    APIResponse, PeerGroupResponse, PeerActivitySubmitSchema, PeerReviewSubmitSchema
)
from app.models.models import User

router = APIRouter()

class AutoGroupRequest(BaseModel):
    cohort_id: uuid.UUID
    strategy: str = "random" # random, balanced
    group_size: int = 5

class SubmitReviewRequest(BaseModel):
    target_submission_id: uuid.UUID
    is_task: bool
    review: PeerReviewSubmitSchema

@router.get("/my-group", response_model=APIResponse[Any])
async def get_my_group(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch teammate details and performance profiles for the logged-in student."""
    group_data = await PeerService.get_my_peer_group(db, current_user.id)
    if not group_data:
        return APIResponse(success=True, data=None, message="You are not assigned to a peer group yet.")
    return APIResponse(success=True, data=group_data)

@router.post("/activities/submit", response_model=APIResponse[Any])
async def submit_activity(
    body: PeerActivitySubmitSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Submit deliverables for peer group assignments."""
    sub = await PeerService.submit_peer_activity(db, current_user, body)
    return APIResponse(success=True, data=None, message="Evidence submitted for teammate review.")

@router.post("/reviews/submit", response_model=APIResponse[Any])
async def submit_review(
    body: SubmitReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Evaluate and submit review feedback for teammate deliverables."""
    review = await PeerService.submit_peer_review(
        db, current_user, body.target_submission_id, body.is_task, body.review
    )
    return APIResponse(success=True, data=None, message="Teammate peer review submitted successfully.")

@router.post("/admin/auto-group", response_model=APIResponse[bool])
async def auto_group_students(
    body: AutoGroupRequest,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Trigger round-robin grouping of students who are unassigned in a cohort."""
    await PeerService.create_peer_groups_automatically(
        db, body.cohort_id, body.strategy, body.group_size
    )
    return APIResponse(success=True, data=True, message="Auto grouping of cohort students completed.")
