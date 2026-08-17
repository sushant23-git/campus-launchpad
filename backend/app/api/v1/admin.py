from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
from datetime import datetime
import uuid

from app.database.session import get_db
from app.api.v1.deps import get_current_user, check_role
from app.services.analytics_service import AnalyticsService
from app.engines.xp import XPEngine
from app.schemas.schemas import APIResponse, XPAdjustmentSchema, AuditLogResponse
from app.models.models import User, AuditLog
from sqlalchemy.future import select

router = APIRouter()

@router.get("/analytics", response_model=APIResponse[Any])
async def get_cohort_analytics(
    cohort_id: uuid.UUID,
    current_user: User = Depends(check_role(["admin", "mentor"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch aggregated performance, backlog and activity metrics for a cohort."""
    stats = await AnalyticsService.get_cohort_analytics(db, cohort_id)
    return APIResponse(success=True, data=stats)

@router.get("/export/students")
async def export_students(
    cohort_id: uuid.UUID,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Download student profile metrics, streaks, and grades as a CSV file."""
    csv_data = await AnalyticsService.export_student_performance_csv(db, cohort_id)
    headers = {
        "Content-Disposition": f"attachment; filename=cohort_{cohort_id}_students.csv"
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)

@router.get("/export/submissions")
async def export_submissions(
    cohort_id: uuid.UUID,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Download all student submissions and review statuses as a CSV file."""
    csv_data = await AnalyticsService.export_submissions_csv(db, cohort_id)
    headers = {
        "Content-Disposition": f"attachment; filename=cohort_{cohort_id}_submissions.csv"
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)

@router.post("/xp/adjust", response_model=APIResponse[Any])
async def adjust_student_xp(
    body: XPAdjustmentSchema,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Perform a controlled administrative XP adjustment, writing to the audit log."""
    tx = await XPEngine.adjust_xp_manually(db, body.student_id, body.points, body.reason)
    
    # Log to audit trail
    log = AuditLog(
        actor_id=current_user.id,
        action="XP_MANUAL_ADJUSTMENT",
        entity_type="UserProfile",
        entity_id=body.student_id,
        payload={"points": body.points, "reason": body.reason, "tx_id": str(tx.id)},
        timestamp=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    return APIResponse(success=True, data=None, message="Student XP corrected and adjustment logged.")

@router.get("/audit-logs", response_model=APIResponse[List[AuditLogResponse]])
async def get_audit_logs(
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
) -> Any:
    """Retrieve system audit logs for administrative overview."""
    result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit))
    logs = result.scalars().all()
    resp = [AuditLogResponse.from_orm(l) for l in logs]
    return APIResponse(success=True, data=resp)
