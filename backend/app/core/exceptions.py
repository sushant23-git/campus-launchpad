from fastapi import HTTPException, status

class CampusLaunchpadException(HTTPException):
    """Base exception for all Campus Launchpad domain errors."""
    code: str = "INTERNAL_SERVER_ERROR"
    
    def __init__(self, status_code: int, detail: str, code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        if code:
            self.code = code

class AuthenticationException(CampusLaunchpadException):
    def __init__(self, detail: str = "Could not validate credentials."):
        super().__init__(
            status_code=status.HTTP_412_PRECONDITION_FAILED, # or 401
            detail=detail,
            code="UNAUTHORIZED"
        )

class InvalidCredentialsException(CampusLaunchpadException):
    def __init__(self, detail: str = "Incorrect email or password."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="INVALID_CREDENTIALS"
        )

class TokenExpiredException(CampusLaunchpadException):
    def __init__(self, detail: str = "Token has expired."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="TOKEN_EXPIRED"
        )

class AccountDisabledException(CampusLaunchpadException):
    def __init__(self, detail: str = "Account is disabled."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="ACCOUNT_DISABLED"
        )

class ForbiddenException(CampusLaunchpadException):
    def __init__(self, detail: str = "You do not have permission to access this resource."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="FORBIDDEN"
        )

class NotFoundException(CampusLaunchpadException):
    def __init__(self, detail: str = "Resource not found."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code="RESOURCE_NOT_FOUND"
        )

class ConflictException(CampusLaunchpadException):
    def __init__(self, detail: str = "Resource conflict."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            code="RESOURCE_CONFLICT"
        )

class BusinessRuleException(CampusLaunchpadException):
    def __init__(self, detail: str = "Business rule violation."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code="BUSINESS_RULE_VIOLATION"
        )
