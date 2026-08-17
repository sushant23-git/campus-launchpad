from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid
from pydantic import BaseModel

from app.database.session import get_db
from app.api.v1.deps import get_current_user
from app.ai.pipeline import AIPipeline
from app.engines.risk import RiskEngine
from app.schemas.schemas import APIResponse, AIInsightResponse
from app.models.models import User, AIInsight
from sqlalchemy.future import select

router = APIRouter()

class GenerateInsightRequest(BaseModel):
    week_number: int

@router.get("/insights", response_model=APIResponse[Any])
async def get_latest_insights(
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch the latest generated AI insights and recommendations for a student."""
    result = await db.execute(
        select(AIInsight)
        .filter(AIInsight.student_id == current_user.id)
        .order_by(AIInsight.generated_at.desc())
    )
    insight = result.scalars().first()
    
    if not insight:
        # Trigger on-the-fly generation if none exists yet
        insight = await AIPipeline.generate_student_insights(db, current_user.id, week_number)

    resp = AIInsightResponse.from_orm(insight)
    return APIResponse(success=True, data=resp)

@router.post("/insights/generate", response_model=APIResponse[Any])
async def trigger_insights_generation(
    body: GenerateInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Trigger insights calculation and evaluation of at-risk warnings."""
    # 1. Run at-risk check
    await RiskEngine.evaluate_student_risk(db, current_user.id, body.week_number)
    
    # 2. Compile AI recommendation
    insight = await AIPipeline.generate_student_insights(db, current_user.id, body.week_number)
    
    resp = AIInsightResponse.from_orm(insight)
    return APIResponse(success=True, data=resp, message="AI insights and risk evaluations completed.")
