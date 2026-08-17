import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List

from app.models.models import RiskFlag, UserProfile, ProgressMetrics, Submission, Task, ConsistencyRecord
from app.services.notification_service import NotificationService

class RiskEngine:
    @staticmethod
    async def evaluate_student_risk(db: AsyncSession, student_id: uuid.UUID, week_number: int) -> Optional[RiskFlag]:
        """Run deterministic rules to evaluate and flag student at-risk levels and interventions."""
        # Load profile
        profile_res = await db.execute(
            select(UserProfile).filter(UserProfile.user_id == student_id)
        )
        profile = profile_res.scalar_one_or_none()
        if not profile:
            return None

        risk_level = "Low"
        reasons = []
        interventions = []
        metrics_summary = {}

        # Rule 1: Check Inactivity
        last_active_str = profile.selected_domains.get("last_active_date")
        if last_active_str:
            last_active_date = datetime.strptime(last_active_str, "%Y-%m-%d").date()
            days_inactive = (date.today() - last_active_date).days
        else:
            days_inactive = 14 # default high if never active
            
        metrics_summary["days_inactive"] = days_inactive
        if days_inactive > 7:
            risk_level = "High"
            reasons.append(f"Student has been inactive for {days_inactive} days.")
            interventions.append("Reach out via email or Discord to check on student availability.")
        elif days_inactive > 4:
            risk_level = "Medium"
            reasons.append(f"Student has been inactive for {days_inactive} days.")
            interventions.append("Send a gentle automated in-app nudge to check in.")

        # Rule 2: Fetch latest progress metrics
        prog_res = await db.execute(
            select(ProgressMetrics).filter(
                ProgressMetrics.student_id == student_id,
                ProgressMetrics.week_number == week_number
            )
        )
        metrics = prog_res.scalar_one_or_none()

        if metrics:
            metrics_summary["overall_progress"] = metrics.overall_progress
            metrics_summary["assessment_score"] = metrics.assessment_score
            metrics_summary["task_score"] = metrics.task_score
            
            # If week 3+ and overall progress is lagging
            if week_number >= 3 and metrics.overall_progress < 40.0:
                risk_level = "High" if risk_level != "High" else risk_level
                reasons.append(f"Overall week progress is lagging at {metrics.overall_progress:.1f}%.")
                interventions.append("Schedule a 1-on-1 mentor guidance review session.")
            elif week_number >= 3 and metrics.overall_progress < 60.0:
                if risk_level == "Low":
                    risk_level = "Medium"
                reasons.append(f"Overall week progress is trailing at {metrics.overall_progress:.1f}%.")
                interventions.append("Recommend the student focus on backlog mandatory tasks.")

            # Rule 3: Low assessment performance
            if metrics.assessment_score < 50.0:
                if risk_level == "Low":
                    risk_level = "Medium"
                reasons.append(f"Assessment performance score is low ({metrics.assessment_score:.1f}%).")
                interventions.append("Suggest reviewing coding concept guides and attempting mock practice quizzes.")

        # Rule 4: Overdue/Missed deadlines
        overdue_res = await db.execute(
            select(Submission).join(Task).filter(
                Submission.student_id == student_id,
                Submission.status.in_(["Assigned", "Started"]),
                Task.deadline < datetime.utcnow()
            )
        )
        overdue_subs = overdue_res.scalars().all()
        metrics_summary["overdue_submissions"] = len(overdue_subs)
        
        if len(overdue_subs) >= 3:
            risk_level = "High"
            reasons.append(f"Student has {len(overdue_subs)} overdue mandatory task submissions.")
            interventions.append("Request immediate submission of missing assignments or apply code freeze overrides.")
        elif len(overdue_subs) >= 1:
            if risk_level == "Low":
                risk_level = "Medium"
            reasons.append(f"Student has {len(overdue_subs)} overdue task submissions.")
            interventions.append("Remind student about approaching task deadlines.")

        # 3. Load existing RiskFlag
        flag_res = await db.execute(
            select(RiskFlag).filter(
                RiskFlag.student_id == student_id,
                RiskFlag.is_resolved == False
            )
        )
        flag = flag_res.scalar_one_or_none()

        if risk_level in ["Medium", "High"]:
            reason_str = " | ".join(reasons)
            interv_str = " | ".join(interventions)
            
            if not flag:
                flag = RiskFlag(
                    student_id=student_id,
                    risk_level=risk_level,
                    reason=reason_str,
                    supporting_metrics=metrics_summary,
                    recommended_intervention=interv_str,
                    is_resolved=False,
                    created_at=datetime.utcnow()
                )
                db.add(flag)
                
                # Notify student of warnings softly
                await NotificationService.create_notification(
                    db, student_id,
                    title="Action Required: Progress Support",
                    message="Our engines detected a drop in your consistency. Let us help you get back on track!",
                    notification_type="Alert"
                )
            else:
                flag.risk_level = risk_level
                flag.reason = reason_str
                flag.supporting_metrics = metrics_summary
                flag.recommended_intervention = interv_str
        else:
            # Low risk: Resolve any active warnings
            if flag:
                flag.is_resolved = True
                flag.resolved_at = datetime.utcnow()
                
                await NotificationService.create_notification(
                    db, student_id,
                    title="Progress Restored!",
                    message="Great job! Your active check-ins have resolved all consistency alerts.",
                    notification_type="Info"
                )

        await db.flush()
        return flag if risk_level in ["Medium", "High"] else None
