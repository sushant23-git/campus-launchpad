import pytest
import uuid
from app.models.models import User, UserProfile
from app.engines.xp import XPEngine
from app.core.exceptions import BusinessRuleException

@pytest.mark.asyncio
async def test_award_xp_success(db_session):
    # 1. Arrange: Create mock user and profile
    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        email="test_student@example.com",
        password_hash="hashed_placeholder_pw",
        role="student",
        is_active=True
    )
    mock_profile = UserProfile(
        user_id=user_id,
        full_name="Test Student",
        xp=0,
        level=1
    )
    db_session.add(mock_user)
    db_session.add(mock_profile)
    await db_session.flush()

    # 2. Act: Award XP
    source_id = uuid.uuid4()
    tx = await XPEngine.award_xp(
        db=db_session,
        student_id=user_id,
        source_type="Task",
        source_id=source_id,
        points=150,
        reason="Completed Week 2 Core Coding Assignment"
    )

    # 3. Assert
    assert tx.points == 150
    assert mock_profile.xp == 150
    assert mock_profile.level == 2 # 150 XP crosses Level 2 Learner threshold (100 XP)

@pytest.mark.asyncio
async def test_award_xp_anti_farming(db_session):
    # 1. Arrange: Create mock user and profile
    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        email="anti_farm@example.com",
        password_hash="hashed_placeholder_pw",
        role="student",
        is_active=True
    )
    mock_profile = UserProfile(
        user_id=user_id,
        full_name="Anti Farm Student",
        xp=0,
        level=1
    )
    db_session.add(mock_user)
    db_session.add(mock_profile)
    await db_session.flush()

    # 2. Act: Award XP first time
    source_id = uuid.uuid4()
    await XPEngine.award_xp(
        db=db_session,
        student_id=user_id,
        source_type="Task",
        source_id=source_id,
        points=100,
        reason="First attempt"
    )

    # 3. Act & Assert: Award second time using same source_id should fail
    with pytest.raises(BusinessRuleException) as exc_info:
        await XPEngine.award_xp(
            db=db_session,
            student_id=user_id,
            source_type="Task",
            source_id=source_id,
            points=100,
            reason="Second farming attempt"
        )
    
    assert "already awarded" in str(exc_info.value.detail)
    assert mock_profile.xp == 100 # score remains unchanged
