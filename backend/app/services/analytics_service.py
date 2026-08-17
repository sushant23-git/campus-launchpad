import uuid
import csv
import io
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any

from app.models.models import (
    User, UserProfile, CohortMember, Submission, Task, ProgressMetrics, RiskFlag
)

class AnalyticsService:
    @staticmethod
    async def get_cohort_analytics(db: AsyncSession, cohort_id: uuid.UUID) -> dict:
        """Aggregate performance statistics, inactivity, and submission backlogs for a cohort."""
        # 1. Total Students in Cohort
        total_students_res = await db.execute(
            select(func.count(CohortMember.id)).filter(CohortMember.cohort_id == cohort_id)
        )
        total_students = total_students_res.scalar() or 0

        # Load student IDs
        stud_ids_res = await db.execute(
            select(CohortMember.student_id).filter(CohortMember.cohort_id == cohort_id)
        )
        student_ids = stud_ids_res.scalars().all()

        if not student_ids:
            return {
                "total_students": 0,
                "active_students": 0,
                "average_xp": 0.0,
                "average_progress": 0.0,
                "submission_backlog": 0,
                "at_risk_students": 0
            }

        # 2. Active Students (Logged in within the last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_res = await db.execute(
            select(func.count(User.id)).filter(
                User.id.in_(student_ids),
                User.updated_at >= week_ago
            )
        )
        active_students = active_res.scalar() or 0

        # 3. Average XP
        xp_res = await db.execute(
            select(func.avg(UserProfile.xp)).filter(UserProfile.user_id.in_(student_ids))
        )
        average_xp = float(xp_res.scalar() or 0.0)

        # 4. Average Progress (Latest recorded week progress metrics)
        prog_res = await db.execute(
            select(func.avg(ProgressMetrics.overall_progress)).filter(
                ProgressMetrics.student_id.in_(student_ids)
            )
        )
        average_progress = float(prog_res.scalar() or 0.0)

        # 5. Submission Backlog (Under Review or Submitted tasks)
        backlog_res = await db.execute(
            select(func.count(Submission.id)).filter(
                Submission.student_id.in_(student_ids),
                Submission.status.in_(["Submitted", "Under_Review"])
            )
        )
        submission_backlog = backlog_res.scalar() or 0

        # 6. At Risk Students Count
        risk_res = await db.execute(
            select(func.count(RiskFlag.id)).filter(
                RiskFlag.student_id.in_(student_ids),
                RiskFlag.is_resolved == False
            )
        )
        at_risk_students = risk_res.scalar() or 0

        return {
            "total_students": total_students,
            "active_students": active_students,
            "average_xp": round(average_xp, 2),
            "average_progress": round(average_progress, 2),
            "submission_backlog": submission_backlog,
            "at_risk_students": at_risk_students
        }

    @staticmethod
    async def export_student_performance_csv(db: AsyncSession, cohort_id: uuid.UUID) -> str:
        """Generate a CSV string of all students' grades, XP, streaks, and progress metrics."""
        query = (
            select(User, UserProfile, CohortMember)
            .join(UserProfile, UserProfile.user_id == User.id)
            .join(CohortMember, CohortMember.student_id == User.id)
            .filter(CohortMember.cohort_id == cohort_id)
        )
        res = await db.execute(query)
        rows = res.all()

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Student ID", "Full Name", "Email", "College Name", "Branch", "Year",
            "Total XP", "Level", "Current Streak", "Profile Completed", "Joined At"
        ])

        for user, profile, member in rows:
            writer.writerow([
                str(user.id),
                profile.full_name,
                user.email,
                profile.college_name or "",
                profile.branch or "",
                profile.year or "",
                profile.xp,
                profile.level,
                profile.current_streak,
                "Yes" if profile.profile_completed else "No",
                member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        return output.getvalue()

    @staticmethod
    async def export_submissions_csv(db: AsyncSession, cohort_id: uuid.UUID) -> str:
        """Generate a CSV string of all submissions in the cohort for auditing."""
        query = (
            select(Submission, Task, User, UserProfile)
            .join(Task, Task.id == Submission.task_id)
            .join(User, User.id == Submission.student_id)
            .join(UserProfile, UserProfile.user_id == User.id)
            .join(CohortMember, CohortMember.student_id == User.id)
            .filter(CohortMember.cohort_id == cohort_id)
            .order_by(Submission.submitted_at.desc())
        )
        res = await db.execute(query)
        rows = res.all()

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Submission ID", "Task ID", "Task Title", "Student Name", "Student Email",
            "Version", "Status", "Score", "Feedback", "Submitted At", "Reviewed At"
        ])

        for sub, task, user, profile in rows:
            writer.writerow([
                str(sub.id),
                str(task.id),
                task.title,
                profile.full_name,
                user.email,
                sub.current_version,
                sub.status,
                sub.score if sub.score is not None else "",
                sub.feedback or "",
                sub.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                sub.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if sub.reviewed_at else ""
            ])

        return output.getvalue()
