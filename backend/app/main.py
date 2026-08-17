from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import CampusLaunchpadException
from app.api.v1.auth import router as auth_router
from app.api.v1.curriculum import router as curriculum_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.quizzes import router as quizzes_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.peers import router as peers_router
from app.api.v1.projects import router as projects_router
from app.api.v1.github import router as github_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.schemas.schemas import APIResponse

app = FastAPI(
    title="Campus Launchpad API",
    description="Full-Stack Student Collaboration and Educational Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Exception Handlers

@app.exception_handler(CampusLaunchpadException)
async def campus_launchpad_exception_handler(request: Request, exc: CampusLaunchpadException):
    """Handler for customized application domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.detail
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for request parsing / schema validation errors."""
    errors = exc.errors()
    # Chain validation failure messages
    msg = "Validation failed: " + "; ".join(
        [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors]
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": msg
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler to prevent raw python stack traces from leaking."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected error occurred on the server: {str(exc)}"
            }
        }
    )

# Register routers under versioned api prefix
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(curriculum_router, prefix="/api/v1/curriculum", tags=["Curriculum"])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(quizzes_router, prefix="/api/v1/quizzes", tags=["Quizzes"])
app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(peers_router, prefix="/api/v1/peers", tags=["Peers"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(github_router, prefix="/api/v1/github", tags=["GitHub"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin Overrides"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Insights"])

@app.get("/health", response_model=APIResponse[str])
async def health_check():
    """Simple API health check endpoint."""
    return APIResponse(success=True, data="healthy", message="Campus Launchpad API is up and running.")
