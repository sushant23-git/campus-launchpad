from fastapi import APIRouter, Depends, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List

from app.database.session import get_db
from app.api.v1.deps import get_current_user, check_role
from app.services.auth_service import AuthService
from app.schemas.schemas import (
    APIResponse, UserRegister, UserLogin, TokenResponse, UserResponse,
    UserProfileResponse, ErrorResponseDetail
)
from app.models.models import User
from pydantic import BaseModel

router = APIRouter()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class VerifyTOTPRequest(BaseModel):
    code: str

@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(schema: UserRegister, db: AsyncSession = Depends(get_db)) -> Any:
    """Register a new student and create their profile."""
    user = await AuthService.register_user(db, schema)
    user_resp = UserResponse.from_orm(user)
    return APIResponse(success=True, data=user_resp, message="User registered successfully.")

@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(schema: UserLogin, db: AsyncSession = Depends(get_db)) -> Any:
    """Authenticate email and password and returns access/refresh tokens."""
    tokens = await AuthService.authenticate_user(db, schema)
    return APIResponse(success=True, data=tokens, message="Login successful.")

@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> Any:
    """Refresh session using a valid refresh token."""
    tokens = await AuthService.refresh_tokens(db, body.refresh_token)
    return APIResponse(success=True, data=tokens, message="Token refreshed successfully.")

@router.post("/logout", response_model=APIResponse[None])
async def logout() -> Any:
    """Log out current user (client should discard local tokens)."""
    return APIResponse(success=True, data=None, message="Logged out successfully.")

@router.get("/me", response_model=APIResponse[UserResponse])
async def read_current_user(current_user: User = Depends(get_current_user)) -> Any:
    """Fetch profile data of the currently logged in user."""
    user_resp = UserResponse.from_orm(current_user)
    return APIResponse(success=True, data=user_resp)

@router.post("/totp/setup", response_model=APIResponse[str])
async def setup_totp(
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Enroll admin in 2FA and retrieve Google Authenticator provisioning URI."""
    uri = await AuthService.generate_totp_provisioning(db, current_user.id)
    return APIResponse(success=True, data=uri, message="Provisioning URI generated.")

@router.post("/totp/verify", response_model=APIResponse[bool])
async def verify_totp(
    body: VerifyTOTPRequest,
    current_user: User = Depends(check_role(["admin"])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Verify code from Google Authenticator to enable 2FA on the account."""
    success = await AuthService.verify_and_enable_totp(db, current_user.id, body.code)
    if success:
        return APIResponse(success=True, data=True, message="TOTP 2FA enabled successfully.")
    return APIResponse(
        success=False,
        data=False,
        error=ErrorResponseDetail(code="INVALID_2FA_CODE", message="The verification code is incorrect.")
    )

class OnboardRequest(BaseModel):
    full_name: str
    college_name: str
    branch: str
    year: str
    skills: List[str]
    interests: List[str]

@router.post("/onboard", response_model=APIResponse[UserProfileResponse])
async def onboard(
    body: OnboardRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Complete profile onboarding for the student."""
    from sqlalchemy.future import select
    from app.models.models import UserProfile
    from typing import List
    from datetime import datetime
    
    result = await db.execute(select(UserProfile).filter(UserProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            full_name=body.full_name,
            college_name=body.college_name,
            branch=body.branch,
            bio="",
            skills={},
            interests={},
            goals={},
            selected_domains={}
        )
        db.add(profile)
        await db.flush()
        
    profile.full_name = body.full_name
    profile.college_name = body.college_name
    profile.branch = body.branch
    
    # Try parsing year
    try:
        if "first" in body.year.lower():
            profile.year = 1
        elif "second" in body.year.lower():
            profile.year = 2
        elif "third" in body.year.lower():
            profile.year = 3
        elif "fourth" in body.year.lower():
            profile.year = 4
        else:
            profile.year = int(body.year)
    except Exception:
        profile.year = 1
        
    profile.skills = {"list": body.skills}
    profile.interests = {"list": body.interests}
    profile.profile_completed = True
    profile.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(profile)
    
    return APIResponse(
        success=True,
        data=UserProfileResponse.from_orm(profile),
        message="Profile completed successfully."
    )
