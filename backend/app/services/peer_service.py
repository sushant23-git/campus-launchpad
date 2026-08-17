import uuid
import random
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.models import (
    PeerGroup, PeerGroupMember, User, UserProfile, PeerActivity,
    PeerActivitySubmission, PeerReview, ActivityEvent, Submission
)
from app.schemas.schemas import PeerActivitySubmitSchema, PeerReviewSubmitSchema
from app.core.exceptions import NotFoundException, BusinessRuleException, ForbiddenException
from app.engines.xp import XPEngine

class PeerService:
    @staticmethod
    async def create_peer_groups_automatically(
        db: AsyncSession,
        cohort_id: uuid.UUID,
        strategy: str = "random", # random, balanced
        group_size: int = 5
    ) -> List[PeerGroup]:
        """Automatically distribute students of a cohort into peer groups using selected strategy."""
        # 1. Fetch all students in the cohort who do not have a peer group
        from app.models.models import CohortMember
        
        # Select all student IDs in cohort
        cohort_students_query = select(CohortMember.student_id).filter(CohortMember.cohort_id == cohort_id)
        cohort_student_ids = (await db.execute(cohort_students_query)).scalars().all()
        
        if not cohort_student_ids:
            raise BusinessRuleException("No students found in this cohort to group.")

        # Filter out students already in a peer group
        grouped_query = select(PeerGroupMember.student_id)
        grouped_student_ids = (await db.execute(grouped_query)).scalars().all()
        
        eligible_student_ids = list(set(cohort_student_ids) - set(grouped_student_ids))
        if not eligible_student_ids:
            return [] # All students are already assigned

        # Load profiles for sorting
        profiles_res = await db.execute(
            select(UserProfile).filter(UserProfile.user_id.in_(eligible_student_ids))
        )
        profiles = {p.user_id: p for p in profiles_res.scalars().all()}

        # Sort/distribute depending on strategy
        if strategy == "balanced":
            # Sort by experience/xp or skill counts to balance teams
            # We estimate skill level by length of profiles.skills dictionary
            sorted_students = sorted(
                eligible_student_ids,
                key=lambda uid: len(profiles[uid].skills) if uid in profiles else 0,
                reverse=True
            )
        else:
            # Random strategy
            sorted_students = eligible_student_ids.copy()
            random.shuffle(sorted_students)

        # 2. Chunk list into groups of size group_size
        num_groups = max(1, len(sorted_students) // group_size)
        groups = []
        for i in range(num_groups):
            g = PeerGroup(
                cohort_id=cohort_id,
                name=f"Peer Group {i + 1}",
                max_members=group_size + 1
            )
            db.add(g)
            groups.append(g)
        await db.flush() # Populate group.id

        # Round-robin distribute students to groups to balance skills
        for idx, student_id in enumerate(sorted_students):
            g_idx = idx % num_groups
            member = PeerGroupMember(
                peer_group_id=groups[g_idx].id,
                student_id=student_id,
                joined_at=datetime.utcnow()
            )
            db.add(member)

        await db.commit()
        return groups

    @staticmethod
    async def get_my_peer_group(db: AsyncSession, student_id: uuid.UUID) -> Optional[dict]:
        """Fetch group name and details of teammates for the logged-in student."""
        # Find group ID for student
        member_res = await db.execute(
            select(PeerGroupMember).filter(PeerGroupMember.student_id == student_id)
        )
        member = member_res.scalar_one_or_none()
        if not member:
            return None

        # Fetch group details and teammates
        group_res = await db.execute(
            select(PeerGroup)
            .filter(PeerGroup.id == member.peer_group_id)
            .options(
                selectinload(PeerGroup.peer_group_members)
                .selectinload(PeerGroupMember.student)
                .selectinload(User.profile)
            )
        )
        group = group_res.scalar_one_or_none()
        if not group:
            return None

        members_list = []
        for m in group.peer_group_members:
            members_list.append({
                "student_id": m.student_id,
                "full_name": m.student.profile.full_name if m.student.profile else "Teammate",
                "role": m.student.role,
                "xp": m.student.profile.xp if m.student.profile else 0,
                "level": m.student.profile.level if m.student.profile else 1
            })

        return {
            "id": group.id,
            "name": group.name,
            "max_members": group.max_members,
            "members": members_list
        }

    @staticmethod
    async def submit_peer_activity(
        db: AsyncSession,
        student: User,
        schema: PeerActivitySubmitSchema
    ) -> PeerActivitySubmission:
        """Submit text explanation or URLs for peer verification."""
        # Check if activity exists
        act_res = await db.execute(select(PeerActivity).filter(PeerActivity.id == schema.peer_activity_id))
        activity = act_res.scalar_one_or_none()
        if not activity:
            raise NotFoundException("Peer activity could not be found.")

        # Check existing submission
        sub_res = await db.execute(
            select(PeerActivitySubmission).filter(
                PeerActivitySubmission.peer_activity_id == schema.peer_activity_id,
                PeerActivitySubmission.student_id == student.id
            )
        )
        submission = sub_res.scalar_one_or_none()

        if submission:
            if submission.status in ["Confirmed", "Approved"]:
                raise BusinessRuleException("Activity already verified and completed.")
            submission.submission_text = schema.submission_text
            submission.evidence_url = schema.evidence_url
            submission.status = "Submitted"
            submission.submitted_at = datetime.utcnow()
        else:
            submission = PeerActivitySubmission(
                peer_activity_id=schema.peer_activity_id,
                student_id=student.id,
                submission_text=schema.submission_text,
                evidence_url=schema.evidence_url,
                status="Submitted",
                submitted_at=datetime.utcnow()
            )
            db.add(submission)

        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def submit_peer_review(
        db: AsyncSession,
        reviewer: User,
        target_submission_id: uuid.UUID,
        is_task: bool, # True if reviewing task, False if peer_activity
        schema: PeerReviewSubmitSchema
    ) -> PeerReview:
        """Submit review for teammate. Awards XP to reviewer and confirmed XP to target student."""
        # Check if reviewer is in same peer group as target student
        if is_task:
            sub_res = await db.execute(select(Submission).filter(Submission.id == target_submission_id))
            target_sub = sub_res.scalar_one_or_none()
            if not target_sub:
                raise NotFoundException("Task submission not found.")
            target_student_id = target_sub.student_id
        else:
            sub_res = await db.execute(select(PeerActivitySubmission).filter(PeerActivitySubmission.id == target_submission_id))
            target_sub = sub_res.scalar_one_or_none()
            if not target_sub:
                raise NotFoundException("Activity submission not found.")
            target_student_id = target_sub.student_id

        # Verify teammates
        rev_group_res = await db.execute(select(PeerGroupMember.peer_group_id).filter(PeerGroupMember.student_id == reviewer.id))
        rev_group_id = rev_group_res.scalar_one_or_none()

        trg_group_res = await db.execute(select(PeerGroupMember.peer_group_id).filter(PeerGroupMember.student_id == target_student_id))
        trg_group_id = trg_group_res.scalar_one_or_none()

        if not rev_group_id or rev_group_id != trg_group_id:
            raise ForbiddenException("You can only review work submitted by your peer group teammates.")

        # Prevent self-reviewing
        if reviewer.id == target_student_id:
            raise BusinessRuleException("You cannot review your own submissions.")

        # Verify anti-farming caps: e.g., max 3 peer reviews rewarded per student per week
        # (check XP transaction logs for peer review rewards in the last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        xp_res = await db.execute(
            select(PeerReview).filter(
                PeerReview.reviewer_id == reviewer.id,
                PeerReview.verified_at >= week_ago
            )
        )
        reviews_count = len(xp_res.scalars().all())
        reviewer_xp_reward = 25 if reviews_count < 3 else 0 # Cap at 3 reviews XP per week

        # Create review
        review = PeerReview(
            peer_submission_id=None if is_task else target_submission_id,
            task_submission_id=target_submission_id if is_task else None,
            reviewer_id=reviewer.id,
            score=schema.score,
            feedback=schema.feedback,
            verified_at=datetime.utcnow(),
            reviewer_xp_rewarded=reviewer_xp_reward
        )
        db.add(review)

        # Reciprocal XP award:
        # 1. Award Reviewer XP (if under cap limit)
        if reviewer_xp_reward > 0:
            await XPEngine.award_xp(
                db, reviewer.id,
                source_type="Peer_Contribution",
                source_id=review.id,
                points=reviewer_xp_reward,
                reason="Teammate peer review contribution"
            )

        # 2. Update target submission status and award target student XP
        if is_task:
            # Tasks are evaluated manually or auto, peer reviews serve as feedback
            # Target gets completed XP when reviewed if peer review confirms completion
            pass
        else:
            # Confirm activity submission
            target_sub.status = "Confirmed"
            # Fetch peer activity XP
            act_res = await db.execute(select(PeerActivity).filter(PeerActivity.id == target_sub.peer_activity_id))
            activity = act_res.scalar_one_or_none()
            xp_reward = activity.xp_reward if activity else 50
            
            # Award points to teammate
            await XPEngine.award_xp(
                db, target_student_id,
                source_type="Peer_Activity",
                source_id=target_sub.id,
                points=xp_reward,
                reason="Teammate confirmed peer activity"
            )

        # Log Activity Event
        event = ActivityEvent(
            user_id=reviewer.id,
            event_type="PEER_REVIEW_SUBMITTED",
            entity_type="PeerReview",
            entity_id=review.id,
            payload={"target_student_id": str(target_student_id), "reviewer_xp": reviewer_xp_reward}
        )
        db.add(event)

        await db.commit()
        await db.refresh(review)
        return review
