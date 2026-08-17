import uuid
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models.models import RankingSnapshot, ProgressMetrics, User, UserProfile
from app.schemas.schemas import LeaderboardEntry

class RankingEngine:
    @staticmethod
    async def compile_weekly_rankings(
        db: AsyncSession,
        cohort_id: uuid.UUID,
        week_number: int
    ) -> List[RankingSnapshot]:
        """Compile and freeze rankings for all students in a cohort for a specific week."""
        # 1. Fetch latest progress metrics for all users in the cohort
        # We can join users, profiles, and progress metrics
        query = (
            select(User, ProgressMetrics)
            .join(ProgressMetrics, ProgressMetrics.student_id == User.id)
            .filter(
                User.is_active == True,
                User.role == "student",
                ProgressMetrics.week_number == week_number
            )
        )
        res = await db.execute(query)
        students_metrics = res.all()

        if not students_metrics:
            return []

        # 2. Calculate weighted scores
        # Formula: Assessment 30% + Project 30% + Tasks 20% + Consistency 10% + Peer 10%
        scores = []
        for user, metrics in students_metrics:
            weighted_score = (
                metrics.assessment_score * 0.30 +
                metrics.project_score * 0.30 +
                metrics.task_score * 0.20 +
                metrics.consistency_score * 0.10 +
                metrics.peer_score * 0.10
            )
            scores.append({
                "student_id": user.id,
                "score": weighted_score
            })

        # 3. Sort students by weighted score descending to determine rank
        scores.sort(key=lambda x: x["score"], reverse=True)

        snapshots = []
        for index, item in enumerate(scores):
            rank = index + 1
            student_id = item["student_id"]
            overall_score = item["score"]

            # Check if there is an existing snapshot for this student and week
            snap_res = await db.execute(
                select(RankingSnapshot).filter(
                    RankingSnapshot.student_id == student_id,
                    RankingSnapshot.week_number == week_number
                )
            )
            snapshot = snap_res.scalar_one_or_none()

            if not snapshot:
                snapshot = RankingSnapshot(
                    student_id=student_id,
                    overall_score=overall_score,
                    rank=rank,
                    week_number=week_number,
                    calculated_at=datetime.utcnow()
                )
                db.add(snapshot)
            else:
                snapshot.overall_score = overall_score
                snapshot.rank = rank
                snapshot.calculated_at = datetime.utcnow()

            snapshots.append(snapshot)

        await db.flush()
        return snapshots

    @staticmethod
    async def get_leaderboard(
        db: AsyncSession,
        week_number: int,
        limit: int = 50
    ) -> List[LeaderboardEntry]:
        """Generate paginated list of top performing students with rank movement indicators."""
        # Join User, UserProfile, and RankingSnapshot
        query = (
            select(User, UserProfile, RankingSnapshot)
            .join(UserProfile, UserProfile.user_id == User.id)
            .join(RankingSnapshot, RankingSnapshot.student_id == User.id)
            .filter(RankingSnapshot.week_number == week_number)
            .order_by(RankingSnapshot.rank)
            .limit(limit)
        )
        res = await db.execute(query)
        rows = res.all()

        entries = []
        for user, profile, snap in rows:
            # Calculate rank movement by fetching previous week's rank
            prev_rank_res = await db.execute(
                select(RankingSnapshot.rank).filter(
                    RankingSnapshot.student_id == user.id,
                    RankingSnapshot.week_number == week_number - 1
                )
            )
            prev_rank = prev_rank_res.scalar_one_or_none()
            
            # Rank movement: positive if rank improved (number decreased), e.g. from 5 to 3 (+2)
            movement = 0
            if prev_rank:
                movement = prev_rank - snap.rank

            entries.append(LeaderboardEntry(
                rank=snap.rank,
                student_id=user.id,
                full_name=profile.full_name,
                xp=profile.xp,
                level=profile.level,
                overall_progress=snap.overall_score, # overall weighted score
                streak=profile.current_streak,
                rank_movement=movement
            ))

        return entries
