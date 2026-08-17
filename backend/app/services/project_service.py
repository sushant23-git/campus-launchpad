import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any

from app.models.models import (
    Domain, DomainExploration, Project, ProjectTeam, ProjectMember,
    ProjectMilestone, ProjectSubmission, User, ActivityEvent, Cohort
)
from app.schemas.schemas import ProjectSubmissionSchema
from app.core.exceptions import NotFoundException, BusinessRuleException, ForbiddenException
from app.engines.xp import XPEngine

class ProjectService:
    # --- DOMAINS EXPLORATION ---
    @staticmethod
    async def get_all_domains(db: AsyncSession) -> List[Domain]:
        """Fetch all technical domains configured in the database."""
        result = await db.execute(select(Domain).order_by(Domain.name))
        return result.scalars().all()

    @staticmethod
    async def get_student_domain_explorations(db: AsyncSession, student_id: uuid.UUID) -> List[dict]:
        """Fetch domains and check student exploration/challenge completion status."""
        result = await db.execute(
            select(DomainExploration)
            .filter(DomainExploration.student_id == student_id)
            .options(selectinload(DomainExploration.domain))
        )
        explorations = result.scalars().all()
        
        explorations_data = []
        for exp in explorations:
            explorations_data.append({
                "domain_id": exp.domain_id,
                "name": exp.domain.name,
                "description": exp.domain.description,
                "status": exp.status, # Explored, Active, Completed
                "mini_challenge_submission_url": exp.mini_challenge_submission_url,
                "mini_challenge_score": exp.mini_challenge_score,
                "explored_at": exp.explored_at,
                "completed_at": exp.completed_at
            })
        return explorations_data

    @staticmethod
    async def start_domain_exploration(db: AsyncSession, student_id: uuid.UUID, domain_id: uuid.UUID) -> DomainExploration:
        """Register domain exploration activity, establishing domain interest profile."""
        # Validate domain
        res = await db.execute(select(Domain).filter(Domain.id == domain_id))
        domain = res.scalar_one_or_none()
        if not domain:
            raise NotFoundException("Domain not found.")

        # Check existing exploration
        exp_res = await db.execute(
            select(DomainExploration).filter(
                DomainExploration.student_id == student_id,
                DomainExploration.domain_id == domain_id
            )
        )
        exploration = exp_res.scalar_one_or_none()

        if not exploration:
            exploration = DomainExploration(
                student_id=student_id,
                domain_id=domain_id,
                status="Explored",
                explored_at=datetime.utcnow()
            )
            db.add(exploration)
            
            # Log Activity Event
            event = ActivityEvent(
                user_id=student_id,
                event_type="DOMAIN_EXPLORED",
                entity_type="Domain",
                entity_id=domain_id
            )
            db.add(event)
            await db.commit()
            
        return exploration

    @staticmethod
    async def submit_domain_mini_challenge(
        db: AsyncSession,
        student_id: uuid.UUID,
        domain_id: uuid.UUID,
        submission_url: str
    ) -> DomainExploration:
        """Submit domain mini-challenge, awarding domain completion XP."""
        # Find exploration
        exp_res = await db.execute(
            select(DomainExploration).filter(
                DomainExploration.student_id == student_id,
                DomainExploration.domain_id == domain_id
            )
        )
        exploration = exp_res.scalar_one_or_none()
        if not exploration:
            # Auto-explore if not registered
            exploration = DomainExploration(
                student_id=student_id,
                domain_id=domain_id,
                status="Explored",
                explored_at=datetime.utcnow()
            )
            db.add(exploration)
            await db.flush()

        if exploration.status == "Completed":
            raise BusinessRuleException("You have already completed the challenge for this domain.")

        # Update exploration
        exploration.status = "Completed"
        exploration.mini_challenge_submission_url = submission_url
        exploration.completed_at = datetime.utcnow()

        # Award XP for Domain Mini-Challenge completion (75 XP from Week 5 metrics)
        await XPEngine.award_xp(
            db, student_id,
            source_type="Domain_Exploration",
            source_id=exploration.id,
            points=75,
            reason="Completed domain mini challenge"
        )

        # Log Activity Event
        event = ActivityEvent(
            user_id=student_id,
            event_type="DOMAIN_CHALLENGE_COMPLETED",
            entity_type="DomainExploration",
            entity_id=exploration.id,
            payload={"submission_url": submission_url}
        )
        db.add(event)
        
        await db.commit()
        return exploration


    # --- PROJECTS ---
    @staticmethod
    async def get_projects_for_student(db: AsyncSession, student: User) -> List[dict]:
        """Fetch major projects. Enforces anonymous presentation details for students."""
        result = await db.execute(select(Project).order_by(Project.project_code))
        projects = result.scalars().all()

        anonymize = student.role == "student"
        projects_data = []
        for project in projects:
            title = f"Project {project.project_code}" if anonymize and project.visibility == "Anonymous" else project.title
            desc = f"Industry: {project.problem_source_type}. Real-world problem statement exploring {project.domain}." if anonymize and project.visibility == "Anonymous" else project.description
            
            projects_data.append({
                "id": project.id,
                "project_code": project.project_code,
                "title": title,
                "description": desc,
                "domain": project.domain,
                "difficulty": project.difficulty,
                "required_skills": project.required_skills,
                "visibility": project.visibility,
                "status": project.status,
                "problem_source_type": "Anonymous Partner" if anonymize and project.visibility == "Anonymous" else project.problem_source_type
            })
        return projects_data

    @staticmethod
    async def create_project_team(
        db: AsyncSession,
        project_id: uuid.UUID,
        team_name: str,
        cohort_id: uuid.UUID,
        members_roles: Dict[uuid.UUID, str] # student_id: role
    ) -> ProjectTeam:
        """Create project team and maps roles, verifying size bounds (4-6 members)."""
        # Validate cohort exists
        c_res = await db.execute(select(Cohort).filter(Cohort.id == cohort_id))
        if not c_res.scalar_one_or_none():
            raise NotFoundException("Cohort not found.")

        # Validate team size (4-6 members)
        if len(members_roles) < 4 or len(members_roles) > 6:
            raise BusinessRuleException("Project team size must be between 4 and 6 members.")

        # Verify students are not already on another active team
        student_ids = list(members_roles.keys())
        existing_mem_res = await db.execute(
            select(ProjectMember).filter(ProjectMember.student_id.in_(student_ids))
        )
        if existing_mem_res.scalars().first():
            raise ConflictException("One or more students are already assigned to a project team.")

        # Create project team
        team = ProjectTeam(
            project_id=project_id,
            name=team_name,
            cohort_id=cohort_id,
            status="Active"
        )
        db.add(team)
        await db.flush() # Populate team.id

        # Create project members
        for s_id, role in members_roles.items():
            member = ProjectMember(
                project_team_id=team.id,
                student_id=s_id,
                role=role,
                joined_at=datetime.utcnow()
            )
            db.add(member)

        # Log Activity Event
        event = ActivityEvent(
            user_id=None,
            event_type="PROJECT_TEAM_CREATED",
            entity_type="ProjectTeam",
            entity_id=team.id,
            payload={"team_name": team_name, "project_id": str(project_id)}
        )
        db.add(event)

        await db.commit()
        return team

    @staticmethod
    async def submit_milestone_delivery(
        db: AsyncSession,
        student: User,
        schema: ProjectSubmissionSchema
    ) -> ProjectSubmission:
        """Process project milestone deliverables for the team."""
        # Verify student belongs to the team
        mem_res = await db.execute(
            select(ProjectMember).filter(
                ProjectMember.student_id == student.id,
                ProjectMember.project_team_id == schema.project_team_id
            )
        )
        if not mem_res.scalar_one_or_none():
            raise ForbiddenException("You are not a member of this project team.")

        # Check existing submission
        sub_res = await db.execute(
            select(ProjectSubmission).filter(
                ProjectSubmission.project_team_id == schema.project_team_id,
                ProjectSubmission.milestone_id == schema.milestone_id
            )
        )
        submission = sub_res.scalar_one_or_none()

        if submission:
            if submission.status == "Evaluated":
                raise BusinessRuleException("Milestone deliverables already evaluated and locked.")
            submission.submission_url = schema.submission_url
            submission.github_pr_url = schema.github_pr_url
            submission.submitted_at = datetime.utcnow()
            submission.status = "Submitted"
        else:
            submission = ProjectSubmission(
                project_team_id=schema.project_team_id,
                milestone_id=schema.milestone_id,
                submission_url=schema.submission_url,
                github_pr_url=schema.github_pr_url,
                status="Submitted",
                submitted_at=datetime.utcnow()
            )
            db.add(submission)

        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def grade_milestone_submission(
        db: AsyncSession,
        reviewer: User,
        submission_id: uuid.UUID,
        score: float,
        feedback: str
    ) -> ProjectSubmission:
        """Evaluate a milestone submission. Awards XP collectively to all team members."""
        result = await db.execute(
            select(ProjectSubmission)
            .filter(ProjectSubmission.id == submission_id)
            .options(selectinload(ProjectSubmission.milestone))
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise NotFoundException("Project submission not found.")

        if submission.status == "Evaluated":
            raise BusinessRuleException("Submission has already been evaluated.")

        # Grade details
        submission.status = "Evaluated"
        submission.score = score
        submission.feedback = feedback
        submission.reviewer_id = reviewer.id
        submission.reviewed_at = datetime.utcnow()

        # Load milestone details to get XP reward
        milestone = submission.milestone
        xp_reward = milestone.xp_reward if milestone else 150

        # Load all team members
        members_res = await db.execute(
            select(ProjectMember).filter(ProjectMember.project_team_id == submission.project_team_id)
        )
        members = members_res.scalars().all()

        # Award milestone XP collectively to all team members!
        for member in members:
            await XPEngine.award_xp(
                db, member.student_id,
                source_type="Milestone",
                source_id=submission.id,
                points=xp_reward,
                reason=f"Completed project milestone: {milestone.title}"
            )

        # Log Activity Event
        event = ActivityEvent(
            user_id=None,
            event_type="PROJECT_MILESTONE_EVALUATED",
            entity_type="ProjectSubmission",
            entity_id=submission.id,
            payload={"reviewer_id": str(reviewer.id), "score": score, "xp_rewarded": xp_reward}
        )
        db.add(event)

        await db.commit()
        await db.refresh(submission)
        return submission
