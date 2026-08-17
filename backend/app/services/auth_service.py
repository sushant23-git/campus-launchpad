import uuid
import pyotp
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.core import security
from app.core.exceptions import (
    InvalidCredentialsException, ConflictException, ForbiddenException, NotFoundException,
    TokenExpiredException, AuthenticationException
)
from app.models.models import User, UserProfile
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse
from jose import JWTError

class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, schema: UserRegister) -> User:
        """Register a new student, hashes their password and initializes profile."""
        # Check if email already exists
        result = await db.execute(select(User).filter(User.email == schema.email))
        if result.scalar_one_or_none():
            raise ConflictException("A user with this email already exists.")
        
        # Hash password and create User
        hashed_password = security.get_password_hash(schema.password)
        db_user = User(
            email=schema.email,
            password_hash=hashed_password,
            role="student", # Default to student for public registration
            is_active=True,
            is_verified=False
        )
        db.add(db_user)
        await db.flush() # Fetch db_user.id for user profile association

        # Initialize student profile
        db_profile = UserProfile(
            user_id=db_user.id,
            full_name=schema.full_name,
            college_name=schema.college_name,
            branch=schema.branch,
            year=schema.year,
            bio="",
            skills={},
            interests={},
            goals={},
            selected_domains={}
        )
        db.add(db_profile)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, schema: UserLogin) -> TokenResponse:
        """Authenticate user credentials and handles admin 2FA verification."""
        result = await db.execute(select(User).filter(User.email == schema.email))
        user = result.scalar_one_or_none()
        
        if not user or not security.verify_password(schema.password, user.password_hash):
            raise InvalidCredentialsException()

        # Admin role requires TOTP verification if configured
        if user.role == "admin" and user.is_totp_enabled:
            if not schema.totp_code:
                raise ForbiddenException("2FA TOTP code is required for administrator accounts.")
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(schema.totp_code):
                raise InvalidCredentialsException("Invalid 2FA code.")

        # Generate tokens
        access_token = security.create_access_token(user.id, user.role)
        refresh_token = security.create_refresh_token(user.id, user.role)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    @staticmethod
    async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
        """Verify refresh token and returns rotated Access & Refresh tokens."""
        try:
            payload = security.decode_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
            user_id_str = payload.get("sub")
            token_type = payload.get("type")
            if not user_id_str or token_type != "refresh":
                raise AuthenticationException("Invalid token type.")
            
            user_uuid = uuid.UUID(user_id_str)
        except (JWTError, ValueError):
            raise AuthenticationException("Invalid or expired refresh token.")

        result = await db.execute(select(User).filter(User.id == user_uuid))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationException("User account is disabled or inactive.")

        # Generate rotated tokens
        new_access_token = security.create_access_token(user.id, user.role)
        new_refresh_token = security.create_refresh_token(user.id, user.role)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )

    @staticmethod
    async def generate_totp_provisioning(db: AsyncSession, user_id: uuid.UUID) -> str:
        """Setup 2FA: generates key secret and returns provisioning URI."""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User account could not be found.")

        # Generate secret
        totp_secret = pyotp.random_base32()
        user.totp_secret = totp_secret
        user.is_totp_enabled = False # Mark False until verified once
        await db.commit()

        totp = pyotp.TOTP(totp_secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=settings.TOTP_ISSUER
        )
        return provisioning_uri

    @staticmethod
    async def verify_and_enable_totp(db: AsyncSession, user_id: uuid.UUID, code: str) -> bool:
        """Verify initial TOTP code to confirm scanner configuration and activates 2FA."""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.totp_secret:
            raise NotFoundException("User 2FA credentials not initialized.")

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code):
            user.is_totp_enabled = True
            await db.commit()
            return True
        return False
