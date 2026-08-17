import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import UploadFile

from app.models.models import Task, Submission, SubmissionVersion, SubmissionFile, Week, User, ActivityEvent
from app.schemas.schemas import TaskSubmitSchema, SubmissionReviewSchema
from app.core.exceptions import NotFoundException, BusinessRuleException, ForbiddenException
from app.services.curriculum_service import CurriculumService
from app.core.storage import get_storage_provider

class TaskService:
    @staticmethod
    async def get_tasks_for_student(db: AsyncSession, student: User, week_id: Optional[uuid.UUID] = None) -> List[dict]:
        """Fetch list of tasks with current submission status, checking unlock constraints."""
        query = select(Task).filter(Task.is_published == True)
        if week_id:
            query = query.filter(Task.week_id == week_id)
        
        result = await db.execute(query.order_by(Task.sequence))
        tasks = result.scalars().all()
        
        tasks_list = []
        for task in tasks:
            # Check if week is locked
            week_result = await db.execute(select(Week).filter(Week.id == task.week_id))
            week = week_result.scalar_one_or_none()
            
            is_locked = False
            lock_reason = ""
            if week:
                is_locked, lock_reason = await CurriculumService.is_week_locked_for_student(db, week, student)

            # Get student's latest submission for this task
            sub_result = await db.execute(
                select(Submission)
                .filter(Submission.task_id == task.id, Submission.student_id == student.id)
            )
            sub = sub_result.scalar_one_or_none()
            
            status = sub.status if sub else "Assigned"
            score = sub.score if sub else None
            feedback = sub.feedback if sub else None

            tasks_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "week_id": task.week_id,
                "module_id": task.module_id,
                "category": task.category,
                "difficulty": task.difficulty,
                "is_mandatory": task.is_mandatory,
                "xp_reward": task.xp_reward,
                "deadline": task.deadline,
                "estimated_time_minutes": task.estimated_time_minutes,
                "submission_type": task.submission_type,
                "evaluation_method": task.evaluation_method,
                "sequence": task.sequence,
                "is_locked": is_locked,
                "lock_reason": lock_reason,
                "submission_status": status,
                "score": score,
                "feedback": feedback
            })
            
        return tasks_list

    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: uuid.UUID, student: User) -> dict:
        """Fetch task details and checking locking rules."""
        result = await db.execute(select(Task).filter(Task.id == task_id, Task.is_published == True))
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundException("Task could not be found.")

        # Check lock state
        week_result = await db.execute(select(Week).filter(Week.id == task.week_id))
        week = week_result.scalar_one_or_none()
        
        is_locked = False
        lock_reason = ""
        if week:
            is_locked, lock_reason = await CurriculumService.is_week_locked_for_student(db, week, student)
            if is_locked:
                raise ForbiddenException(f"Task is locked: {lock_reason}")

        # Fetch submissions
        sub_result = await db.execute(
            select(Submission)
            .filter(Submission.task_id == task.id, Submission.student_id == student.id)
            .options(selectinload(Submission.versions))
        )
        sub = sub_result.scalar_one_or_none()

        return {
            "task": task,
            "submission": sub,
            "is_locked": is_locked,
            "lock_reason": lock_reason
        }

    @staticmethod
    async def submit_task(
        db: AsyncSession, 
        student: User, 
        task_id: uuid.UUID, 
        content: str, 
        file: Optional[UploadFile] = None
    ) -> Submission:
        """Process new task submission, maintaining revision versions securely."""
        # Validate task exists & unlocked
        result = await db.execute(select(Task).filter(Task.id == task_id, Task.is_published == True))
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundException("Task could not be found.")

        week_result = await db.execute(select(Week).filter(Week.id == task.week_id))
        week = week_result.scalar_one_or_none()
        if week:
            is_locked, lock_reason = await CurriculumService.is_week_locked_for_student(db, week, student)
            if is_locked:
                raise BusinessRuleException(f"Cannot submit task. Week is locked: {lock_reason}")

        # Enforce deadline restriction (can submit late, but flags it)
        is_late = datetime.utcnow() > task.deadline

        # Get existing submission
        sub_query = select(Submission).filter(
            Submission.task_id == task_id,
            Submission.student_id == student.id
        )
        sub_res = await db.execute(sub_query)
        submission = sub_res.scalar_one_or_none()

        # Handle submission files if provided
        file_meta = None
        if file:
            storage = get_storage_provider()
            file_name, storage_path = storage.save_file(file)
            file_meta = {
                "file_name": file.filename,
                "file_path": storage_path,
                "mime_type": file.content_type,
                "file_size": os.path.getsize(storage_path) if os.path.exists(storage_path) else 0
            }

        if not submission:
            # First time submission
            submission = Submission(
                task_id=task_id,
                student_id=student.id,
                current_version=1,
                status="Submitted" if task.evaluation_method == "Manual" else "Completed",
                score=None,
                feedback=None
            )
            db.add(submission)
            await db.flush()

            sub_version = SubmissionVersion(
                submission_id=submission.id,
                version=1,
                content=content,
                status=submission.status,
                submitted_at=datetime.utcnow()
            )
            db.add(sub_version)
        else:
            # Re-submission
            # Prevent re-submitting approved work unless administrative overrides are set
            if submission.status == "Approved" or submission.status == "Completed":
                raise BusinessRuleException("Approved or completed tasks cannot be re-submitted.")

            submission.current_version += 1
            submission.status = "Submitted" if task.evaluation_method == "Manual" else "Completed"
            submission.updated_at = datetime.utcnow()

            sub_version = SubmissionVersion(
                submission_id=submission.id,
                version=submission.current_version,
                content=content,
                status=submission.status,
                submitted_at=datetime.utcnow()
            )
            db.add(sub_version)

        # Associate file metadata to submission
        if file_meta:
            db_file = SubmissionFile(
                submission_id=submission.id,
                file_name=file_meta["file_name"],
                file_path=file_meta["file_path"],
                mime_type=file_meta["mime_type"],
                file_size=file_meta["file_size"]
            )
            db.add(db_file)

        # Log Activity Event
        event = ActivityEvent(
            user_id=student.id,
            event_type="TASK_SUBMITTED",
            entity_type="Submission",
            entity_id=submission.id,
            payload={"version": submission.current_version, "is_late": is_late}
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def review_submission(
        db: AsyncSession,
        reviewer: User,
        submission_id: uuid.UUID,
        schema: SubmissionReviewSchema
    ) -> Submission:
        """Allows mentor/admin to grade a submission and record evaluation outcomes."""
        result = await db.execute(
            select(Submission)
            .filter(Submission.id == submission_id)
            .options(selectinload(Submission.versions))
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise NotFoundException("Submission could not be found.")

        # Update submission status
        submission.status = schema.status # Approved, Rejected, Revision_Requested
        submission.score = schema.score
        submission.feedback = schema.feedback
        submission.reviewer_id = reviewer.id
        submission.reviewed_at = datetime.utcnow()

        # Update latest submission version record as well
        for version in submission.versions:
            if version.version == submission.current_version:
                version.status = schema.status
                version.score = schema.score
                version.feedback = schema.feedback
                version.reviewer_id = reviewer.id
                version.reviewed_at = datetime.utcnow()

        # Log Activity Event
        event = ActivityEvent(
            user_id=submission.student_id,
            event_type=f"TASK_{schema.status.upper()}",
            entity_type="Submission",
            entity_id=submission.id,
            payload={"reviewer_id": str(reviewer.id), "score": schema.score}
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(submission)
        return submission
