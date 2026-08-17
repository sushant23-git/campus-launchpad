import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import ProgressMetrics, Task, Submission, Quiz, QuizAttempt, PeerActivity, PeerActivitySubmission, ProjectSubmission, ProjectMember, ProjectMilestone, Week, ConsistencyRecord

class ProgressEngine:
    @staticmethod
    async def recalculate_student_metrics(
        db: AsyncSession,
        student_id: uuid.UUID,
        week_number: int
    ) -> ProgressMetrics:
        """Calculate and update student progress percentages for a specific week."""
        # 1. Fetch Week Entity
        week_res = await db.execute(select(Week).filter(Week.week_number == week_number))
        week = week_res.scalar_one_or_none()
        if not week:
            # Fallback mock if week not found
            overall_progress = 0.0
            task_score = 0.0
            assessment_score = 0.0
            peer_score = 0.0
            project_score = 0.0
            consistency_score = 0.0
        else:
            # 2. Task Score Calculation (Mandatory tasks completed)
            t_res = await db.execute(
                select(Task.id).filter(
                    Task.week_id == week.id,
                    Task.is_mandatory == True,
                    Task.is_published == True
                )
            )
            mandatory_task_ids = t_res.scalars().all()
            
            if not mandatory_task_ids:
                task_score = 100.0
            else:
                s_res = await db.execute(
                    select(Submission.task_id).filter(
                        Submission.student_id == student_id,
                        Submission.task_id.in_(mandatory_task_ids),
                        Submission.status == "Approved"
                    )
                )
                completed_task_ids = s_res.scalars().all()
                task_score = (len(completed_task_ids) / len(mandatory_task_ids)) * 100.0

            # 3. Assessment Score Calculation (Highest Quiz score)
            q_res = await db.execute(
                select(Quiz.id).filter(
                    Quiz.week_id == week.id,
                    Quiz.is_published == True
                )
            )
            quiz_ids = q_res.scalars().all()
            
            if not quiz_ids:
                assessment_score = 100.0
            else:
                att_res = await db.execute(
                    select(QuizAttempt.score).filter(
                        QuizAttempt.student_id == student_id,
                        QuizAttempt.quiz_id.in_(quiz_ids),
                        QuizAttempt.status == "Completed"
                    )
                )
                attempts = att_res.scalars().all()
                assessment_score = max(attempts) if attempts else 0.0

            # 4. Peer Activity Score Calculation
            pa_res = await db.execute(
                select(PeerActivity.id).filter(PeerActivity.week_id == week.id)
            )
            peer_activity_ids = pa_res.scalars().all()
            
            if not peer_activity_ids:
                peer_score = 100.0
            else:
                pas_res = await db.execute(
                    select(PeerActivitySubmission.peer_activity_id).filter(
                        PeerActivitySubmission.student_id == student_id,
                        PeerActivitySubmission.peer_activity_id.in_(peer_activity_ids),
                        PeerActivitySubmission.status == "Approved"
                    )
                )
                completed_pas_ids = pas_res.scalars().all()
                peer_score = (len(completed_pas_ids) / len(peer_activity_ids)) * 100.0

            # 5. Project Score Calculation (Based on student project team milestone score)
            # Find student project team
            pm_res = await db.execute(
                select(ProjectMember.project_team_id).filter(ProjectMember.student_id == student_id)
            )
            team_id = pm_res.scalar_one_or_none()
            
            if not team_id:
                project_score = 0.0
            else:
                # Find milestones for this week
                mil_res = await db.execute(
                    select(ProjectMilestone.id).filter(ProjectMilestone.week_number == week_number)
                )
                milestone_ids = mil_res.scalars().all()
                
                if not milestone_ids:
                    # No milestones this week, get team overall project completion
                    project_score = 100.0
                else:
                    pjs_res = await db.execute(
                        select(ProjectSubmission.score).filter(
                            ProjectSubmission.project_team_id == team_id,
                            ProjectSubmission.milestone_id.in_(milestone_ids),
                            ProjectSubmission.status == "Evaluated"
                        )
                    )
                    milestone_scores = pjs_res.scalars().all()
                    project_score = (sum(milestone_scores) / len(milestone_ids)) if milestone_scores else 0.0

            # 6. Consistency Score Calculation (Days active in week / 5 days)
            cons_res = await db.execute(
                select(ConsistencyRecord).filter(
                    ConsistencyRecord.student_id == student_id,
                    ConsistencyRecord.week_number == week_number
                )
            )
            cons = cons_res.scalar_one_or_none()
            consistency_score = (cons.days_active / 5.0 * 100.0) if cons else 0.0
            consistency_score = min(100.0, consistency_score)

        # 7. Calculate overall weighted progress
        # Weighting breakdown:
        # Tasks: 40%, Assessments: 30%, Peer: 10%, Project: 10%, Consistency: 10%
        overall_progress = (
            task_score * 0.40 +
            assessment_score * 0.30 +
            peer_score * 0.10 +
            project_score * 0.10 +
            consistency_score * 0.10
        )

        # 8. Update database record
        metrics_res = await db.execute(
            select(ProgressMetrics).filter(
                ProgressMetrics.student_id == student_id,
                ProgressMetrics.week_number == week_number
            )
        )
        metrics = metrics_res.scalar_one_or_none()

        if not metrics:
            metrics = ProgressMetrics(
                student_id=student_id,
                week_number=week_number,
                task_score=task_score,
                assessment_score=assessment_score,
                peer_score=peer_score,
                project_score=project_score,
                consistency_score=consistency_score,
                overall_progress=overall_progress
            )
            db.add(metrics)
        else:
            metrics.task_score = task_score
            metrics.assessment_score = assessment_score
            metrics.peer_score = peer_score
            metrics.project_score = project_score
            metrics.consistency_score = consistency_score
            metrics.overall_progress = overall_progress
            metrics.updated_at = datetime.utcnow()

        await db.flush()
        return metrics
