from pydantic import BaseModel, EmailStr, Field
from typing import Generic, TypeVar, Optional, Any, List, Dict
from datetime import datetime, date
import uuid

T = TypeVar("T")

# --- UNIFIED RESPONSE ENVELOPES ---

class ErrorResponseDetail(BaseModel):
    code: str
    message: str

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[ErrorResponseDetail] = None

# --- AUTH & USER SCHEMAS ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    college_name: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    college_name: Optional[str]
    branch: Optional[str]
    year: Optional[int]
    bio: Optional[str]
    skills: Dict[str, Any]
    interests: Dict[str, Any]
    goals: Dict[str, Any]
    github_username: Optional[str]
    github_url: Optional[str]
    selected_domains: Dict[str, Any]
    xp: int
    level: int
    current_streak: int
    profile_completed: bool

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    is_verified: bool
    is_totp_enabled: bool
    created_at: datetime
    profile: Optional[UserProfileResponse] = None

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    college_name: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None
    bio: Optional[str] = None
    skills: Optional[Dict[str, Any]] = None
    interests: Optional[Dict[str, Any]] = None
    goals: Optional[Dict[str, Any]] = None
    github_username: Optional[str] = None
    github_url: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

# --- CURRICULUM SCHEMAS ---

class ContentResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    title: str
    description: str
    content_type: str
    body: str
    resource_url: Optional[str]
    estimated_minutes: int
    sequence: int
    is_mandatory: bool

    class Config:
        from_attributes = True

class ContentProgressResponse(BaseModel):
    content_id: uuid.UUID
    is_completed: bool
    duration_seconds: int
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ModuleResponse(BaseModel):
    id: uuid.UUID
    week_id: uuid.UUID
    title: str
    description: str
    sequence: int
    estimated_minutes: int
    is_mandatory: bool
    contents: List[ContentResponse] = []

    class Config:
        from_attributes = True

class WeekResponse(BaseModel):
    id: uuid.UUID
    week_number: int
    title: str
    description: str
    start_date: date
    end_date: date
    unlock_at: datetime
    is_published: bool
    is_mandatory: bool
    modules: List[ModuleResponse] = []

    class Config:
        from_attributes = True

class HeartbeatSchema(BaseModel):
    content_id: uuid.UUID
    duration_seconds: int

# --- TASKS & SUBMISSIONS SCHEMAS ---

class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    week_id: uuid.UUID
    module_id: Optional[uuid.UUID]
    category: str
    difficulty: str
    is_mandatory: bool
    xp_reward: int
    deadline: datetime
    estimated_time_minutes: int
    submission_type: str
    evaluation_method: str
    sequence: int

    class Config:
        from_attributes = True

class SubmissionVersionResponse(BaseModel):
    id: uuid.UUID
    version: int
    content: str
    submitted_at: datetime
    status: str
    score: Optional[float]
    feedback: Optional[str]

    class Config:
        from_attributes = True

class SubmissionResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    student_id: uuid.UUID
    current_version: int
    status: str
    score: Optional[float]
    feedback: Optional[str]
    reviewer_id: Optional[uuid.UUID]
    reviewed_at: Optional[datetime]
    created_at: datetime
    versions: List[SubmissionVersionResponse] = []

    class Config:
        from_attributes = True

class TaskSubmitSchema(BaseModel):
    task_id: uuid.UUID
    content: str

class SubmissionReviewSchema(BaseModel):
    status: str # Approved, Rejected, Revision_Requested
    score: Optional[float] = None
    feedback: Optional[str] = None

# --- QUIZZES SCHEMAS ---

class QuestionOptionSchema(BaseModel):
    label: str # e.g. A, B, C, D
    text: str

class QuestionResponse(BaseModel):
    id: uuid.UUID
    question_type: str
    question_text: str
    options: Optional[List[QuestionOptionSchema]] = None
    marks: float
    sequence: int

    class Config:
        from_attributes = True

class QuizResponse(BaseModel):
    id: uuid.UUID
    week_id: uuid.UUID
    module_id: Optional[uuid.UUID]
    title: str
    description: str
    time_limit_minutes: int
    attempt_limit: int
    passing_score: float

    class Config:
        from_attributes = True

class QuizAttemptResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    student_id: uuid.UUID
    started_at: datetime
    submitted_at: Optional[datetime]
    score: float
    status: str

    class Config:
        from_attributes = True

class QuestionAnswerSchema(BaseModel):
    question_id: uuid.UUID
    selected_options: List[str] # MCQ / MSQ option labels, or text answers

class QuizSubmitSchema(BaseModel):
    attempt_id: uuid.UUID
    answers: List[QuestionAnswerSchema]

# --- PEER SYSTEM SCHEMAS ---

class PeerGroupMemberResponse(BaseModel):
    student_id: uuid.UUID
    full_name: str

class PeerGroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    members: List[PeerGroupMemberResponse] = []

    class Config:
        from_attributes = True

class PeerActivityResponse(BaseModel):
    id: uuid.UUID
    week_id: uuid.UUID
    task: str
    deadline: datetime
    required_participants: int
    xp_reward: int

    class Config:
        from_attributes = True

class PeerActivitySubmitSchema(BaseModel):
    peer_activity_id: uuid.UUID
    submission_text: Optional[str] = None
    evidence_url: Optional[str] = None

class PeerReviewSubmitSchema(BaseModel):
    feedback: str
    score: Optional[float] = None

# --- PROJECT SYSTEM SCHEMAS ---

class ProjectResponse(BaseModel):
    id: uuid.UUID
    project_code: str
    title: str
    description: str
    domain: str
    difficulty: str
    required_skills: Dict[str, Any]
    visibility: str
    problem_source_type: str
    status: str

    class Config:
        from_attributes = True

class ProjectMemberResponse(BaseModel):
    student_id: uuid.UUID
    full_name: str
    role: str

    class Config:
        from_attributes = True

class ProjectTeamResponse(BaseModel):
    id: uuid.UUID
    project_id: Optional[uuid.UUID]
    name: str
    status: str
    members: List[ProjectMemberResponse] = []

    class Config:
        from_attributes = True

class ProjectMilestoneResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str
    week_number: int
    weight: float
    deadline: datetime
    xp_reward: int

    class Config:
        from_attributes = True

class ProjectSubmissionSchema(BaseModel):
    project_team_id: uuid.UUID
    milestone_id: uuid.UUID
    submission_url: Optional[str] = None
    github_pr_url: Optional[str] = None

# --- METRICS & GAMIFICATION ---

class LeaderboardEntry(BaseModel):
    rank: int
    student_id: uuid.UUID
    full_name: str
    xp: int
    level: int
    overall_progress: float
    streak: int
    rank_movement: int # positive, negative, or zero

class ProgressMetricsResponse(BaseModel):
    week_number: int
    task_score: float
    assessment_score: float
    peer_score: float
    project_score: float
    consistency_score: float
    overall_progress: float

    class Config:
        from_attributes = True

class XPTransactionResponse(BaseModel):
    id: uuid.UUID
    source_type: str
    points: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True

class AIInsightResponse(BaseModel):
    insight_type: str
    summary: str
    recommendation: str
    confidence: float
    generated_at: datetime

    class Config:
        from_attributes = True

class RiskFlagResponse(BaseModel):
    risk_level: str
    reason: str
    recommended_intervention: str
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- ADMIN OVERRIDES & AUDIT ---

class XPAdjustmentSchema(BaseModel):
    student_id: uuid.UUID
    points: int
    reason: str

class PeerGroupAssignmentSchema(BaseModel):
    student_id: uuid.UUID
    peer_group_id: uuid.UUID

class ProjectTeamAssignmentSchema(BaseModel):
    student_id: uuid.UUID
    project_team_id: uuid.UUID

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_id: Optional[uuid.UUID]
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID]
    metadata: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True
