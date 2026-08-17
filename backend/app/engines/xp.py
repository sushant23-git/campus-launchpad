import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import XPTransaction, UserProfile, User
from app.core.exceptions import BusinessRuleException

# Level threshold definitions from the product specs
LEVEL_THRESHOLDS = [
    {"level": 1, "name": "Explorer", "min_xp": 0},
    {"level": 2, "name": "Learner", "min_xp": 100},
    {"level": 3, "name": "Builder", "min_xp": 250},
    {"level": 4, "name": "Problem Solver", "min_xp": 500},
    {"level": 5, "name": "Developer", "min_xp": 1000},
    {"level": 6, "name": "Advanced Builder", "min_xp": 2000},
]

class XPEngine:
    @staticmethod
    async def award_xp(
        db: AsyncSession,
        student_id: uuid.UUID,
        source_type: str,
        source_id: Optional[uuid.UUID],
        points: int,
        reason: str
    ) -> XPTransaction:
        """Award XP to a student and update their profile level, validating anti-farming constraints."""
        if points <= 0:
            raise BusinessRuleException("XP points awarded must be positive.")

        # Validate anti-farming rule: one-time reward per source item
        if source_id:
            existing_tx = await db.execute(
                select(XPTransaction).filter(
                    XPTransaction.student_id == student_id,
                    XPTransaction.source_type == source_type,
                    XPTransaction.source_id == source_id
                )
            )
            if existing_tx.scalars().first():
                # Silently return or raise depending on preference. Here we prevent duplicate entry.
                raise BusinessRuleException(f"XP points for this {source_type} already awarded to prevent farming.")

        # Create audit transaction entry
        tx = XPTransaction(
            student_id=student_id,
            source_type=source_type,
            source_id=source_id,
            points=points,
            reason=reason,
            created_at=datetime.utcnow()
        )
        db.add(tx)
        await db.flush()

        # Update User Profile aggregate
        profile_res = await db.execute(
            select(UserProfile).filter(UserProfile.user_id == student_id)
        )
        profile = profile_res.scalar_one_or_none()
        if not profile:
            # Fallback if profile wasn't initialized
            profile = UserProfile(
                user_id=student_id,
                full_name="Student",
                xp=0,
                level=1
            )
            db.add(profile)
            await db.flush()

        # Update cumulative XP
        profile.xp += points

        # Recalculate Level
        new_level = 1
        for threshold in LEVEL_THRESHOLDS:
            if profile.xp >= threshold["min_xp"]:
                new_level = threshold["level"]
        
        profile.level = new_level
        
        # We commit the transaction in the outer call
        return tx

    @staticmethod
    async def adjust_xp_manually(
        db: AsyncSession,
        student_id: uuid.UUID,
        adjustment_points: int,
        reason: str
    ) -> XPTransaction:
        """Controlled administrative override adjustment (positive or negative)."""
        tx = XPTransaction(
            student_id=student_id,
            source_type="Correction",
            source_id=None,
            points=adjustment_points,
            reason=f"Admin Adjustment: {reason}",
            created_at=datetime.utcnow()
        )
        db.add(tx)
        await db.flush()

        profile_res = await db.execute(
            select(UserProfile).filter(UserProfile.user_id == student_id)
        )
        profile = profile_res.scalar_one_or_none()
        if profile:
            profile.xp = max(0, profile.xp + adjustment_points)
            
            # Recalculate Level
            new_level = 1
            for threshold in LEVEL_THRESHOLDS:
                if profile.xp >= threshold["min_xp"]:
                    new_level = threshold["level"]
            profile.level = new_level
            
        return tx
