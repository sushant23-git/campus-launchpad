import uuid
from typing import Optional
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError

from app.core import security
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationException, ForbiddenException, AccountDisabledException
)
from app.database.session import get_db
from app.models.models import User

# Authorization header API key dependency (supporting Bearer tokens)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(api_key_header)
) -> User:
    """Dependency to retrieve and validate the current authenticated user from JWT access token."""
    if not token:
        raise AuthenticationException("Authorization header is missing or empty.")
    
    # Strip Bearer prefix if sent by client
    if token.lower().startswith("bearer "):
        token = token[7:]
        
    try:
        payload = security.decode_token(token, settings.JWT_SECRET_KEY)
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not user_id_str or token_type != "access":
            raise AuthenticationException("Invalid authentication credentials.")
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise AuthenticationException("Could not validate credentials or token expired.")

    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .filter(User.id == user_id)
        .options(selectinload(User.profile))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationException("User account could not be found.")
    if not user.is_active:
        raise AccountDisabledException()
        
    return user

def check_role(required_roles: list[str]):
    """Enforce specific role requirements (RBAC) on an endpoint."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise ForbiddenException("You do not have permissions to perform this action.")
        return current_user
    return dependency
