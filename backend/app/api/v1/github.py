from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.database.session import get_db
from app.api.v1.deps import get_current_user
from app.integrations.github.client import GitHubClient
from app.schemas.schemas import APIResponse
from app.models.models import User, GithubConnection, GithubRepository
from sqlalchemy.future import select

router = APIRouter()

class ConnectGithubSchema(BaseModel):
    github_username: str

@router.post("/connect", response_model=APIResponse[bool])
async def connect_github_account(
    body: ConnectGithubSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Link student's GitHub username to their platform profile."""
    # Check if already connected
    conn_res = await db.execute(
        select(GithubConnection).filter(GithubConnection.student_id == current_user.id)
    )
    conn = conn_res.scalar_one_or_none()
    
    if conn:
        conn.github_username = body.github_username
        conn.connected_at = datetime.utcnow()
    else:
        conn = GithubConnection(
            student_id=current_user.id,
            github_username=body.github_username,
            access_token="mock_token", # Defaults to mock token for dev environment
            connected_at=datetime.utcnow()
        )
        db.add(conn)
        
    # Update profile fields
    if current_user.profile:
        current_user.profile.github_username = body.github_username
        current_user.profile.github_url = f"https://github.com/{body.github_username}"

    await db.commit()
    return APIResponse(success=True, data=True, message="GitHub profile connected successfully.")

@router.post("/sync", response_model=APIResponse[Any])
async def sync_github_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Sync repository events to consistency stats."""
    activities = await GitHubClient.sync_student_repositories(db, current_user.id)
    # Map to printable summary
    sync_data = [{
        "event_type": act.event_type,
        "commit_hash": act.commit_hash,
        "timestamp": act.activity_timestamp
    } for act in activities]
    
    return APIResponse(success=True, data=sync_data, message=f"Synced {len(activities)} new activity events.")
