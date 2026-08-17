import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import ConsistencyRecord, UserProfile, Week
from app.engines.xp import XPEngine

class ConsistencyEngine:
    @staticmethod
    async def record_activity(db: AsyncSession, student_id: uuid.UUID) -> None:
        """Log active login or submissions, incrementing week activity days and updating streaks."""
        # 1. Load Student Profile
        profile_res = await db.execute(
            select(UserProfile).filter(UserProfile.user_id == student_id)
        )
        profile = profile_res.scalar_one_or_none()
        if not profile:
            return

        today_dt = datetime.utcnow()
        today = today_dt.date()

        # Find current week number based on calendar dates
        week_res = await db.execute(
            select(Week)
            .filter(Week.start_date <= today, Week.end_date >= today)
        )
        week = week_res.scalar_one_or_none()
        week_number = week.week_number if week else 1

        # 2. Load or Create Consistency Record for this week
        cons_res = await db.execute(
            select(ConsistencyRecord).filter(
                ConsistencyRecord.student_id == student_id,
                ConsistencyRecord.week_number == week_number
            )
        )
        cons = cons_res.scalar_one_or_none()

        if not cons:
            cons = ConsistencyRecord(
                student_id=student_id,
                week_number=week_number,
                days_active=0,
                streak_count=profile.current_streak,
                on_time_submissions=0,
                created_at=today_dt
            )
            db.add(cons)
            await db.flush()

        # Verify if already active today (compare date of last activity)
        # We can look up in a separate table, or check ConsistencyRecord's update date
        # Let's check when the consistency record was last updated
        last_update_date = cons.created_at.date() if cons.days_active > 0 else None
        
        if last_update_date == today:
            # Already checked in today
            return

        # Increment active days for this week
        cons.days_active += 1
        cons.created_at = today_dt # Mark check-in timestamp

        # 3. Calculate Daily Streak Increment
        # Fetch the last check-in date across the platform by checking when UserProfile was updated
        # (or last activity date from profile metadata, let's store it dynamically in selected_domains/goals)
        last_active_str = profile.selected_domains.get("last_active_date")
        
        if last_active_str:
            last_active_date = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        else:
            last_active_date = None

        if last_active_date == today:
            # Already logged today
            pass
        elif last_active_date == today - timedelta(days=1):
            # Consecutive day! Increment streak
            profile.current_streak += 1
            cons.streak_count = profile.current_streak
            
            # Award Streak Bonus XP
            if profile.current_streak == 3:
                await XPEngine.award_xp(
                    db, student_id,
                    source_type="Bonus",
                    source_id=None,
                    points=15,
                    reason="3-Day Activity Streak Bonus!"
                )
            elif profile.current_streak == 5:
                await XPEngine.award_xp(
                    db, student_id,
                    source_type="Bonus",
                    source_id=None,
                    points=30,
                    reason="5-Day Activity Streak Bonus!"
                )
        else:
            # Broken streak, reset to 1
            profile.current_streak = 1
            cons.streak_count = 1

        # Save check-in metadata
        profile.selected_domains["last_active_date"] = today.strftime("%Y-%m-%d")
        
        await db.flush()
