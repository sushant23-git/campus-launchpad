from fastapi import APIRouter, Depends, status, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Optional
import uuid

from app.database.session import get_db
from app.api.v1.deps import get_current_user, check_role
from app.services.task_service import TaskService
from app.schemas.schemas import APIResponse, SubmissionResponse, SubmissionReviewSchema, TaskResponse
from app.models.models import User

router = APIRouter()

@router.get("", response_model=APIResponse[List[Any]])
async def get_tasks(
    week_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch all tasks for the current student, optional filtering by week ID."""
    tasks = await TaskService.get_tasks_for_student(db, current_user, week_id)
    return APIResponse(success=True, data=tasks)

@router.get("/{task_id}", response_model=APIResponse[Any])
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve details and submission history of a single task."""
    details = await TaskService.get_task_by_id(db, task_id, current_user)
    # Wrap in model dict
    data = {
        "task": TaskResponse.from_orm(details["task"]),
        "submission": SubmissionResponse.from_orm(details["submission"]) if details["submission"] else None,
        "is_locked": details["is_locked"],
        "lock_reason": details["lock_reason"]
    }
    return APIResponse(success=True, data=data)

@router.post("/{task_id}/submit", response_model=APIResponse[Any])
async def submit_task(
    task_id: uuid.UUID,
    content: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Submit a text response, link, or upload files for a specific task."""
    submission = await TaskService.submit_task(db, current_user, task_id, content, file)
    resp = SubmissionResponse.from_orm(submission)
    return APIResponse(success=True, data=resp, message="Task submitted successfully.")

@router.post("/submissions/{submission_id}/review", response_model=APIResponse[Any])
async def review_submission(
    submission_id: uuid.UUID,
    body: SubmissionReviewSchema,
    current_user: User = Depends(check_role(["mentor", "admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Evaluate a student's task submission, marking approval and giving feedback."""
    submission = await TaskService.review_submission(db, current_user, submission_id, body)
    resp = SubmissionResponse.from_orm(submission)
    return APIResponse(success=True, data=resp, message="Submission evaluated successfully.")
