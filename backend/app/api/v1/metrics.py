from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Optional
import uuid

from app.database.session import get_db
from app.api.v1.deps import get_current_user
from app.engines.ranking import RankingEngine
from app.schemas.schemas import (
    APIResponse, LeaderboardEntry, ProgressMetricsResponse, XPTransactionResponse
)
from app.models.models import User, ProgressMetrics, XPTransaction
from sqlalchemy.future import select

router = APIRouter()

@router.get("/leaderboard", response_model=APIResponse[List[LeaderboardEntry]])
async def get_leaderboard(
    week_number: int,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve the paginated student leaderboard for a specific week."""
    leaderboard = await RankingEngine.get_leaderboard(db, week_number, limit)
    return APIResponse(success=True, data=leaderboard)

@router.get("/progress", response_model=APIResponse[List[ProgressMetricsResponse]])
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch weekly progress breakdown statistics for the current student."""
    result = await db.execute(
        select(ProgressMetrics)
        .filter(ProgressMetrics.student_id == current_user.id)
        .order_by(ProgressMetrics.week_number)
    )
    metrics = result.scalars().all()
    resp = [ProgressMetricsResponse.from_orm(m) for m in metrics]
    return APIResponse(success=True, data=resp)

@router.get("/xp", response_model=APIResponse[List[XPTransactionResponse]])
async def get_my_xp_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch auditable XP transaction log for the current student."""
    result = await db.execute(
        select(XPTransaction)
        .filter(XPTransaction.student_id == current_user.id)
        .order_by(XPTransaction.created_at.desc())
    )
    txs = result.scalars().all()
    resp = [XPTransactionResponse.from_orm(t) for t in txs]
    return APIResponse(success=True, data=resp)
