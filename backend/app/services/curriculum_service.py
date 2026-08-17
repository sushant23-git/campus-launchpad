import uuid
from datetime import datetime, date
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.models import Week, Module, Content, ContentProgress, Task, Submission, ActivityEvent, User
from app.schemas.schemas import WeekResponse, ModuleResponse, ContentResponse, HeartbeatSchema
from app.core.exceptions import NotFoundException, BusinessRuleException

class CurriculumService:
    @staticmethod
    async def get_weeks_for_student(db: AsyncSession, student: User) -> List[dict]:
        """Fetch all weeks with modules and content, including lock states and completed status."""
        result = await db.execute(
            select(Week)
            .filter(Week.is_published == True)
            .order_by(Week.week_number)
            .options(
                selectinload(Week.modules)
                .selectinload(Module.contents)
            )
        )
        weeks = result.scalars().all()
        
        weeks_list = []
        for week in weeks:
            is_locked, lock_reason = await CurriculumService.is_week_locked_for_student(db, week, student)
            
            # Check modules progress
            modules_data = []
            for module in week.modules:
                contents_data = []
                for content in module.contents:
                    # Get student content progress
                    progress_result = await db.execute(
                        select(ContentProgress).filter(
                            ContentProgress.user_id == student.id,
                            ContentProgress.content_id == content.id
                        )
                    )
                    progress = progress_result.scalar_one_or_none()
                    is_completed = progress.is_completed if progress else False
                    duration = progress.duration_seconds if progress else 0
                    
                    contents_data.append({
                        "id": content.id,
                        "title": content.title,
                        "description": content.description,
                        "content_type": content.content_type,
                        "body": content.body,
                        "resource_url": content.resource_url,
                        "estimated_minutes": content.estimated_minutes,
                        "sequence": content.sequence,
                        "is_mandatory": content.is_mandatory,
                        "is_completed": is_completed,
                        "duration_seconds": duration
                    })
                
                # Sort contents by sequence
                contents_data.sort(key=lambda x: x["sequence"])
                
                modules_data.append({
                    "id": module.id,
                    "title": module.title,
                    "description": module.description,
                    "sequence": module.sequence,
                    "estimated_minutes": module.estimated_minutes,
                    "is_mandatory": module.is_mandatory,
                    "contents": contents_data
                })
            
            # Sort modules by sequence
            modules_data.sort(key=lambda x: x["sequence"])

            weeks_list.append({
                "id": week.id,
                "week_number": week.week_number,
                "title": week.title,
                "description": week.description,
                "start_date": week.start_date,
                "end_date": week.end_date,
                "unlock_at": week.unlock_at,
                "is_mandatory": week.is_mandatory,
                "is_locked": is_locked,
                "lock_reason": lock_reason,
                "modules": modules_data
            })
            
        return weeks_list

    @staticmethod
    async def is_week_locked_for_student(db: AsyncSession, week: Week, student: User) -> Tuple[bool, str]:
        """Check if a week is locked for a student. Returns (is_locked, reason)."""
        # Admin bypass
        if student.role == "admin":
            return False, ""
            
        # 1. Check if week is published
        if not week.is_published:
            return True, "This week has not been published yet."

        # 2. Check scheduled unlock date
        now = datetime.utcnow()
        if now < week.unlock_at:
            return True, f"This week is scheduled to unlock on {week.unlock_at.strftime('%Y-%m-%d')}."

        # 3. Check if previous mandatory week is completed
        if week.week_number > 1:
            # Fetch previous week
            prev_result = await db.execute(
                select(Week).filter(Week.week_number == week.week_number - 1)
            )
            prev_week = prev_result.scalar_one_or_none()
            
            if prev_week and prev_week.is_mandatory:
                # Find all mandatory tasks in previous week
                tasks_result = await db.execute(
                    select(Task.id).filter(
                        Task.week_id == prev_week.id,
                        Task.is_mandatory == True,
                        Task.is_published == True
                    )
                )
                mandatory_task_ids = tasks_result.scalars().all()
                
                if mandatory_task_ids:
                    # Find student's approved submissions for those tasks
                    subs_result = await db.execute(
                        select(Submission.task_id).filter(
                            Submission.student_id == student.id,
                            Submission.task_id.in_(mandatory_task_ids),
                            Submission.status == "Approved"
                        )
                    )
                    approved_task_ids = subs_result.scalars().all()
                    
                    if len(approved_task_ids) < len(mandatory_task_ids):
                        # Check for admin override (event log)
                        override_result = await db.execute(
                            select(ActivityEvent).filter(
                                ActivityEvent.user_id == student.id,
                                ActivityEvent.event_type == "ADMIN_OVERRIDE_UNLOCK_WEEK",
                                ActivityEvent.entity_id == week.id
                            )
                        )
                        if not override_result.scalars().first():
                            return True, f"Complete all mandatory tasks of Week {week.week_number - 1} to unlock."
                            
        return False, ""

    @staticmethod
    async def track_content_heartbeat(db: AsyncSession, student: User, schema: HeartbeatSchema) -> dict:
        """Register periodic heartbeats for reading content, marking completion under duration limits."""
        # Validate content exists
        result = await db.execute(select(Content).filter(Content.id == schema.content_id))
        content = result.scalar_one_or_none()
        if not content:
            raise NotFoundException("Learning content could not be found.")

        # Prevent duplicate heartbeat abuse (duration should be reasonable, e.g., max 60s per call)
        if schema.duration_seconds <= 0 or schema.duration_seconds > 60:
            raise BusinessRuleException("Invalid heartbeat duration.")

        # Check if week is locked
        week_result = await db.execute(
            select(Week).join(Module).filter(Module.id == content.module_id)
        )
        week = week_result.scalar_one_or_none()
        if week:
            is_locked, reason = await CurriculumService.is_week_locked_for_student(db, week, student)
            if is_locked:
                raise BusinessRuleException(f"Cannot track activity. Content is locked: {reason}")

        # Fetch or create progress
        progress_result = await db.execute(
            select(ContentProgress).filter(
                ContentProgress.user_id == student.id,
                ContentProgress.content_id == content.id
            )
        )
        progress = progress_result.scalar_one_or_none()

        if not progress:
            progress = ContentProgress(
                user_id=student.id,
                content_id=content.id,
                started_at=datetime.utcnow(),
                last_active_at=datetime.utcnow(),
                duration_seconds=0,
                is_completed=False
            )
            db.add(progress)
            await db.flush()

        # Enforce cap on duration_seconds (prevent farming by opening page indefinitely)
        max_duration = content.estimated_minutes * 60 * 3 # Allow max 3x estimated reading time
        if progress.duration_seconds >= max_duration:
            return {
                "is_completed": progress.is_completed,
                "duration_seconds": progress.duration_seconds,
                "message": "Farming cap reached. Activity time ceased."
            }

        # Update heartbeat stats
        progress.duration_seconds += schema.duration_seconds
        progress.last_active_at = datetime.utcnow()

        # Auto-complete content when reading time reaches 75% of estimated minutes
        was_completed = progress.is_completed
        if not progress.is_completed and progress.duration_seconds >= (content.estimated_minutes * 60 * 0.75):
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            
            # Emit Activity Event
            event = ActivityEvent(
                user_id=student.id,
                event_type="MODULE_CONTENT_COMPLETED",
                entity_type="Content",
                entity_id=content.id,
                payload={"duration_seconds": progress.duration_seconds}
            )
            db.add(event)

        await db.commit()
        await db.refresh(progress)

        return {
            "is_completed": progress.is_completed,
            "duration_seconds": progress.duration_seconds,
            "just_completed": (not was_completed and progress.is_completed)
        }
