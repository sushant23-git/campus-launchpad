from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Optional
import uuid
from pydantic import BaseModel

from app.database.session import get_db
from app.api.v1.deps import get_current_user, check_role
from app.services.project_service import ProjectService
from app.schemas.schemas import (
    APIResponse, ProjectResponse, ProjectTeamResponse, ProjectSubmissionSchema,
    ProjectMilestoneResponse
)
from app.models.models import User, ProjectMilestone
from sqlalchemy.future import select

router = APIRouter()

class DomainExploreRequest(BaseModel):
    submission_url: str

class TeamCreateRequest(BaseModel):
    project_id: uuid.UUID
    team_name: str
    cohort_id: uuid.UUID
    members_roles: dict # student_id: role string

class ReviewMilestoneRequest(BaseModel):
    score: float
    feedback: str

@router.get("/domains", response_model=APIResponse[List[Any]])
async def get_domains(db: AsyncSession = Depends(get_db)) -> Any:
    """Fetch list of all technology exploration domains."""
    domains = await ProjectService.get_all_domains(db)
    return APIResponse(success=True, data=domains)

@router.get("/domains/my-explorations", response_model=APIResponse[List[Any]])
async def get_my_explorations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch domains explored by the current student and progress stats."""
    exps = await ProjectService.get_student_domain_explorations(db, current_user.id)
    return APIResponse(success=True, data=exps)

@router.post("/domains/{domain_id}/explore", response_model=APIResponse[Any])
async def explore_domain(
    domain_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Register student's active interest in exploring a technical domain."""
    exp = await ProjectService.start_domain_exploration(db, current_user.id, domain_id)
    return APIResponse(success=True, data=None, message="Domain marked as explored.")

@router.post("/domains/{domain_id}/challenge", response_model=APIResponse[Any])
async def submit_challenge(
    domain_id: uuid.UUID,
    body: DomainExploreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Submit solution url for a domain mini-challenge to earn specialization XP."""
    await ProjectService.submit_domain_mini_challenge(db, current_user.id, domain_id, body.submission_url)
    return APIResponse(success=True, data=None, message="Domain challenge submitted successfully.")

@router.get("", response_model=APIResponse[List[Any]])
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve list of major projects (anonymized initially for student roles)."""
    projects = await ProjectService.get_projects_for_student(db, current_user)
    return APIResponse(success=True, data=projects)

@router.post("/teams/create", response_model=APIResponse[Any])
async def create_team(
    body: TeamCreateRequest,
    current_user: User = Depends(check_role(["mentor", "admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a project team and bind members with specific tech roles."""
    # Convert string keys in dict to UUID
    members_dict = {uuid.UUID(k): v for k, v in body.members_roles.items()}
    team = await ProjectService.create_project_team(
        db, body.project_id, body.team_name, body.cohort_id, members_dict
    )
    resp = ProjectTeamResponse.from_orm(team)
    return APIResponse(success=True, data=resp, message="Project team formed successfully.")

@router.post("/milestones/submit", response_model=APIResponse[Any])
async def submit_milestone(
    body: ProjectSubmissionSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Submit milestone deliverables on behalf of the project team."""
    sub = await ProjectService.submit_milestone_delivery(db, current_user, body)
    return APIResponse(success=True, data=None, message="Milestone deliverables submitted successfully.")

@router.post("/submissions/{submission_id}/review", response_model=APIResponse[Any])
async def review_milestone(
    submission_id: uuid.UUID,
    body: ReviewMilestoneRequest,
    current_user: User = Depends(check_role(["mentor", "admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Evaluate team milestone deliverables, giving score and feedback."""
    sub = await ProjectService.grade_milestone_submission(
        db, current_user, submission_id, body.score, body.feedback
    )
    return APIResponse(success=True, data=None, message="Milestone submission graded and XP distributed.")

@router.get("/milestones", response_model=APIResponse[List[ProjectMilestoneResponse]])
async def get_milestones(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch milestones details for a major project."""
    res = await db.execute(select(ProjectMilestone).filter(ProjectMilestone.project_id == project_id))
    milestones = res.scalars().all()
    resp = [ProjectMilestoneResponse.from_orm(m) for m in milestones]
    return APIResponse(success=True, data=resp)
