import uuid
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from app.models.models import GithubConnection, GithubRepository, GithubActivity, User
from app.engines.consistency import ConsistencyEngine
from app.core.config import settings

class GitHubClient:
    @staticmethod
    async def sync_student_repositories(
        db: AsyncSession,
        student_id: uuid.UUID
    ) -> List[GithubActivity]:
        """Fetch and sync GitHub activity (commits, PRs, issues) for a student."""
        # 1. Fetch connection details
        conn_res = await db.execute(
            select(GithubConnection).filter(GithubConnection.student_id == student_id)
        )
        connection = conn_res.scalar_one_or_none()
        if not connection:
            return [] # No github connected

        # 2. Check if we are running in mock mode
        # If GitHub client secret/token are not set, we simulate activity synchronization
        if settings.GITHUB_CLIENT_SECRET == "your_github_client_secret" or connection.access_token == "mock_token":
            return await GitHubClient._generate_mock_activity(db, connection, student_id)

        # 3. Real integration flow (Http requests to GitHub API)
        activities = []
        async with httpx.AsyncClient() as client:
            # Fetch connected repositories from database
            repos_res = await db.execute(
                select(GithubRepository).filter(GithubRepository.github_connection_id == connection.id)
            )
            repositories = repos_res.scalars().all()

            headers = {
                "Authorization": f"token {connection.access_token}",
                "Accept": "application/vnd.github.v3+json"
            }

            for repo in repositories:
                try:
                    # Fetch repository commits
                    # URL format: https://api.github.com/repos/{owner}/{repo}/events
                    owner_repo = repo.repo_url.replace("https://github.com/", "")
                    api_url = f"https://api.github.com/repos/{owner_repo}/events"
                    
                    response = await client.get(api_url, headers=headers, timeout=10.0)
                    if response.status_code == 200:
                        events = response.json()
                        for event in events:
                            event_type = event.get("type")
                            if event_type not in ["PushEvent", "PullRequestEvent", "IssuesEvent"]:
                                continue

                            # Map event type
                            mapped_type = "Commit" if event_type == "PushEvent" else ("PR" if event_type == "PullRequestEvent" else "Issue")
                            commit_hash = None
                            
                            if mapped_type == "Commit":
                                commits = event.get("payload", {}).get("commits", [])
                                if commits:
                                    commit_hash = commits[0].get("sha")

                            created_at_str = event.get("created_at")
                            activity_time = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ") if created_at_str else datetime.utcnow()

                            # Check if activity already synced (using unique commit hash or event ID)
                            event_id = event.get("id")
                            existing_act = await db.execute(
                                select(GithubActivity).filter(
                                    GithubActivity.repository_id == repo.id,
                                    GithubActivity.student_id == student_id,
                                    GithubActivity.commit_hash == (commit_hash or event_id)
                                )
                            )
                            if existing_act.scalars().first():
                                continue

                            activity = GithubActivity(
                                repository_id=repo.id,
                                student_id=student_id,
                                event_type=mapped_type,
                                commit_hash=commit_hash or event_id,
                                event_metadata=event,
                                activity_timestamp=activity_time,
                                synced_at=datetime.utcnow()
                            )
                            db.add(activity)
                            activities.append(activity)

                            # Record activity for consistency engine check-in
                            await ConsistencyEngine.record_activity(db, student_id)
                except Exception:
                    # Graceful degradation on individual repository failures
                    continue
                    
        await db.commit()
        return activities

    @staticmethod
    async def _generate_mock_activity(
        db: AsyncSession,
        connection: GithubConnection,
        student_id: uuid.UUID
    ) -> List[GithubActivity]:
        """Simulate repo commits for local testing and development."""
        # Find repositories
        repos_res = await db.execute(
            select(GithubRepository).filter(GithubRepository.github_connection_id == connection.id)
        )
        repositories = repos_res.scalars().all()
        if not repositories:
            # Seed a mock repository link
            repo = GithubRepository(
                github_connection_id=connection.id,
                repo_name="noxus-coding-journey",
                repo_url=f"https://github.com/{connection.github_username}/noxus-coding-journey",
                connected_at=datetime.utcnow()
            )
            db.add(repo)
            await db.flush()
            repositories = [repo]

        activities = []
        # Create a mock commit today
        for repo in repositories:
            commit_hash = str(uuid.uuid4())[:8]
            activity = GithubActivity(
                repository_id=repo.id,
                student_id=student_id,
                event_type="Commit",
                commit_hash=commit_hash,
                event_metadata={
                    "message": "Mock commit: Complete weekly task exercise",
                    "committer": connection.github_username
                },
                activity_timestamp=datetime.utcnow(),
                synced_at=datetime.utcnow()
            )
            db.add(activity)
            activities.append(activity)

            # Check in consistency streak today
            await ConsistencyEngine.record_activity(db, student_id)

        await db.flush()
        return activities
