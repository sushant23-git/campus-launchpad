import uuid
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Integer, Float, ForeignKey, DateTime, Date, JSON, Text, UUID
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_model import Base

# --- AUTH & USER MANAGEMENT ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="student") # student, mentor, admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    cohort_members: Mapped[List["CohortMember"]] = relationship("CohortMember", back_populates="student", cascade="all, delete-orphan")
    peer_group_members: Mapped[List["PeerGroupMember"]] = relationship("PeerGroupMember", back_populates="student", cascade="all, delete-orphan")
    submissions: Mapped[List["Submission"]] = relationship("Submission", foreign_keys="[Submission.student_id]", back_populates="student", cascade="all, delete-orphan")
    quiz_attempts: Mapped[List["QuizAttempt"]] = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")
    project_members: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="student", cascade="all, delete-orphan")
    xp_transactions: Mapped[List["XPTransaction"]] = relationship("XPTransaction", back_populates="student", cascade="all, delete-orphan")
    progress_metrics: Mapped[List["ProgressMetrics"]] = relationship("ProgressMetrics", back_populates="student", cascade="all, delete-orphan")
    ranking_snapshots: Mapped[List["RankingSnapshot"]] = relationship("RankingSnapshot", back_populates="student", cascade="all, delete-orphan")
    consistency_records: Mapped[List["ConsistencyRecord"]] = relationship("ConsistencyRecord", back_populates="student", cascade="all, delete-orphan")
    github_connection: Mapped[Optional["GithubConnection"]] = relationship("GithubConnection", back_populates="student", cascade="all, delete-orphan", uselist=False)
    activity_events: Mapped[List["ActivityEvent"]] = relationship("ActivityEvent", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    ai_insights: Mapped[List["AIInsight"]] = relationship("AIInsight", back_populates="student", cascade="all, delete-orphan")
    risk_flags: Mapped[List["RiskFlag"]] = relationship("RiskFlag", back_populates="student", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    college_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[dict] = mapped_column(JSON, default=dict) # JSON list/dictionary of skills & levels
    interests: Mapped[dict] = mapped_column(JSON, default=dict)
    goals: Mapped[dict] = mapped_column(JSON, default=dict)
    github_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    selected_domains: Mapped[dict] = mapped_column(JSON, default=dict) # Explored & primary/secondary interest domains
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")


# --- PROGRAM STRUCTURE ---

class Cohort(Base):
    __tablename__ = "cohorts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    batch_year: Mapped[int] = mapped_column(Integer, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, default=250)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    cohort_members: Mapped[List["CohortMember"]] = relationship("CohortMember", back_populates="cohort", cascade="all, delete-orphan")
    peer_groups: Mapped[List["PeerGroup"]] = relationship("PeerGroup", back_populates="cohort", cascade="all, delete-orphan")
    project_teams: Mapped[List["ProjectTeam"]] = relationship("ProjectTeam", back_populates="cohort", cascade="all, delete-orphan")


class CohortMember(Base):
    __tablename__ = "cohort_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    cohort: Mapped["Cohort"] = relationship("Cohort", back_populates="cohort_members")
    student: Mapped["User"] = relationship("User", back_populates="cohort_members")


class PeerGroup(Base):
    __tablename__ = "peer_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, default=6)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    cohort: Mapped["Cohort"] = relationship("Cohort", back_populates="peer_groups")
    peer_group_members: Mapped[List["PeerGroupMember"]] = relationship("PeerGroupMember", back_populates="peer_group", cascade="all, delete-orphan")
    peer_activities: Mapped[List["PeerActivity"]] = relationship("PeerActivity", back_populates="peer_group", cascade="all, delete-orphan")


class PeerGroupMember(Base):
    __tablename__ = "peer_group_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    peer_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    peer_group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="peer_group_members")
    student: Mapped["User"] = relationship("User", back_populates="peer_group_members")


# --- CURRICULUM ENGINE ---

class Week(Base):
    __tablename__ = "weeks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    unlock_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lock_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    modules: Mapped[List["Module"]] = relationship("Module", back_populates="week", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="week", cascade="all, delete-orphan")
    quizzes: Mapped[List["Quiz"]] = relationship("Quiz", back_populates="week", cascade="all, delete-orphan")
    peer_activities: Mapped[List["PeerActivity"]] = relationship("PeerActivity", back_populates="week", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("weeks.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    week: Mapped["Week"] = relationship("Week", back_populates="modules")
    contents: Mapped[List["Content"]] = relationship("Content", back_populates="module", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="module", cascade="all, delete-orphan")
    quizzes: Mapped[List["Quiz"]] = relationship("Quiz", back_populates="module", cascade="all, delete-orphan")


class Content(Base):
    __tablename__ = "contents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False) # Article, Video, External_Resource, Rich_Text, Code_Example, Checklist
    body: Mapped[str] = mapped_column(Text, nullable=False) # Rich content (Markdown)
    resource_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=10)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    module: Mapped["Module"] = relationship("Module", back_populates="contents")
    progress_records: Mapped[List["ContentProgress"]] = relationship("ContentProgress", back_populates="content", cascade="all, delete-orphan")


class ContentProgress(Base):
    __tablename__ = "content_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    content: Mapped["Content"] = relationship("Content", back_populates="progress_records")


# --- TASK SYSTEM ---

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    week_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("weeks.id", ondelete="CASCADE"), nullable=False)
    module_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False) # Learning, Coding, GitHub, Problem_Solving, Peer_Activity, Assessment, Domain_Exploration, Project, Optional_Challenge
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="Beginner") # Beginner, Intermediate, Advanced
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    estimated_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    submission_type: Mapped[str] = mapped_column(String(100), nullable=False) # GitHub_Link, Repository, URL, Text, File_Upload, Quiz, Project, Peer_Review, Manual_Verification
    evaluation_method: Mapped[str] = mapped_column(String(50), default="Manual") # Auto, Manual
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    week: Mapped["Week"] = relationship("Week", back_populates="tasks")
    module: Mapped[Optional["Module"]] = relationship("Module", back_populates="tasks")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="task", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="Submitted") # Assigned, Started, Submitted, Under_Review, Approved, Rejected, Revision_Requested, Completed
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="submissions")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], back_populates="submissions")
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewer_id])
    versions: Mapped[List["SubmissionVersion"]] = relationship("SubmissionVersion", back_populates="submission", cascade="all, delete-orphan")
    files: Mapped[List["SubmissionFile"]] = relationship("SubmissionFile", back_populates="submission", cascade="all, delete-orphan")
    peer_reviews: Mapped[List["PeerReview"]] = relationship("PeerReview", back_populates="task_submission", cascade="all, delete-orphan")


class SubmissionVersion(Base):
    __tablename__ = "submission_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False) # JSON or Raw text submission content
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="versions")
    reviewer: Mapped[Optional["User"]] = relationship("User")


class SubmissionFile(Base):
    __tablename__ = "submission_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="files")


# --- QUIZ & ASSESSMENT SYSTEM ---

class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=True)
    week_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("weeks.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=30)
    attempt_limit: Mapped[int] = mapped_column(Integer, default=1)
    passing_score: Mapped[float] = mapped_column(Float, default=60.0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    week: Mapped["Week"] = relationship("Week", back_populates="quizzes")
    module: Mapped[Optional["Module"]] = relationship("Module", back_populates="quizzes")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts: Mapped[List["QuizAttempt"]] = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False) # MCQ, MSQ, TF, Short_Answer, Long_Answer
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # List of selectable choices for MCQ/MSQ
    correct_answer: Mapped[dict] = mapped_column(JSON, nullable=False) # List of indices or text
    marks: Mapped[float] = mapped_column(Float, default=1.0)
    sequence: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    answers: Mapped[List["QuizAnswer"]] = relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="In_Progress") # In_Progress, Completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="quiz_attempts")
    answers: Mapped[List["QuizAnswer"]] = relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_options: Mapped[dict] = mapped_column(JSON, default=dict) # Answers submitted by student
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    marks_awarded: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")


# --- PEER GROUP & ACTIVITIES SYSTEM ---

class PeerActivity(Base):
    __tablename__ = "peer_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("weeks.id", ondelete="CASCADE"), nullable=False)
    peer_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=True)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    required_participants: Mapped[int] = mapped_column(Integer, default=2)
    verification_method: Mapped[str] = mapped_column(String(100), nullable=False) # Reciprocal_Confirmation, Admin_Verification
    xp_reward: Mapped[int] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    week: Mapped["Week"] = relationship("Week", back_populates="peer_activities")
    peer_group: Mapped[Optional["PeerGroup"]] = relationship("PeerGroup", back_populates="peer_activities")
    submissions: Mapped[List["PeerActivitySubmission"]] = relationship("PeerActivitySubmission", back_populates="peer_activity", cascade="all, delete-orphan")


class PeerActivitySubmission(Base):
    __tablename__ = "peer_activity_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    peer_activity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("peer_activities.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    submission_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), default="Submitted") # Submitted, Confirmed, Approved, Rejected

    # Relationships
    peer_activity: Mapped["PeerActivity"] = relationship("PeerActivity", back_populates="submissions")
    student: Mapped["User"] = relationship("User")
    reviews: Mapped[List["PeerReview"]] = relationship("PeerReview", back_populates="peer_submission", cascade="all, delete-orphan")


class PeerReview(Base):
    __tablename__ = "peer_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    peer_submission_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("peer_activity_submissions.id", ondelete="CASCADE"), nullable=True)
    task_submission_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewer_xp_rewarded: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    peer_submission: Mapped[Optional["PeerActivitySubmission"]] = relationship("PeerActivitySubmission", back_populates="reviews")
    task_submission: Mapped[Optional["Submission"]] = relationship("Submission", back_populates="peer_reviews")
    reviewer: Mapped["User"] = relationship("User")


# --- DOMAIN EXPLORATION ---

class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills_required: Mapped[dict] = mapped_column(JSON, default=dict)
    beginner_learning_activity: Mapped[str] = mapped_column(Text, nullable=False)
    mini_challenge: Mapped[str] = mapped_column(Text, nullable=False)
    career_opportunities: Mapped[dict] = mapped_column(JSON, default=dict)
    example_roles: Mapped[dict] = mapped_column(JSON, default=dict)
    recommended_tools: Mapped[dict] = mapped_column(JSON, default=dict)
    project_examples: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    explorations: Mapped[List["DomainExploration"]] = relationship("DomainExploration", back_populates="domain", cascade="all, delete-orphan")


class DomainExploration(Base):
    __tablename__ = "domain_explorations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Explored") # Explored, Active, Completed
    mini_challenge_submission_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mini_challenge_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    explored_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    student: Mapped["User"] = relationship("User")
    domain: Mapped["Domain"] = relationship("Domain", back_populates="explorations")


# --- PROJECT SYSTEM ---

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # LP-042
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False) # Beginner, Intermediate, Advanced
    required_skills: Mapped[dict] = mapped_column(JSON, default=dict)
    visibility: Mapped[str] = mapped_column(String(50), default="Anonymous") # Anonymous, Public
    problem_source_type: Mapped[str] = mapped_column(String(100), nullable=False) # Company name or internal sandbox
    status: Mapped[str] = mapped_column(String(50), default="Ideation") # Ideation, Planning, Development, Testing, Demo, Evaluated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    teams: Mapped[List["ProjectTeam"]] = relationship("ProjectTeam", back_populates="project")
    milestones: Mapped[List["ProjectMilestone"]] = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")


class ProjectTeam(Base):
    __tablename__ = "project_teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cohort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False)
    mentor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Active") # Active, Completed, Disbanded
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="teams")
    cohort: Mapped["Cohort"] = relationship("Cohort", back_populates="project_teams")
    mentor: Mapped[Optional["User"]] = relationship("User")
    members: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="project_team", cascade="all, delete-orphan")
    submissions: Mapped[List["ProjectSubmission"]] = relationship("ProjectSubmission", back_populates="project_team", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("project_teams.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False) # Project_Lead, Frontend, Backend, AI_ML, UI_UX, QA, Doc
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project_team: Mapped["ProjectTeam"] = relationship("ProjectTeam", back_populates="members")
    student: Mapped["User"] = relationship("User", back_populates="project_members")


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0) # Weight of milestone score
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=200)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="milestones")
    submissions: Mapped[List["ProjectSubmission"]] = relationship("ProjectSubmission", back_populates="milestone", cascade="all, delete-orphan")


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("project_teams.id", ondelete="CASCADE"), nullable=False)
    milestone_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("project_milestones.id", ondelete="CASCADE"), nullable=False)
    submission_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_pr_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Submitted") # Submitted, Under_Review, Evaluated
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    project_team: Mapped["ProjectTeam"] = relationship("ProjectTeam", back_populates="submissions")
    milestone: Mapped["ProjectMilestone"] = relationship("ProjectMilestone", back_populates="submissions")
    reviewer: Mapped[Optional["User"]] = relationship("User")


# --- METRICS & GAMIFICATION SYSTEM ---

class XPTransaction(Base):
    __tablename__ = "xp_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False) # Task, Quiz, Peer_Activity, Milestone, Domain_Exploration, Bonus, Correction
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True) # References specific activity ID
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="xp_transactions")


class ProgressMetrics(Base):
    __tablename__ = "progress_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    task_score: Mapped[float] = mapped_column(Float, default=0.0)
    assessment_score: Mapped[float] = mapped_column(Float, default=0.0)
    peer_score: Mapped[float] = mapped_column(Float, default=0.0)
    project_score: Mapped[float] = mapped_column(Float, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    overall_progress: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="progress_metrics")


class RankingSnapshot(Base):
    __tablename__ = "ranking_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="ranking_snapshots")


class ConsistencyRecord(Base):
    __tablename__ = "consistency_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    days_active: Mapped[int] = mapped_column(Integer, default=0)
    streak_count: Mapped[int] = mapped_column(Integer, default=0)
    on_time_submissions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="consistency_records")


# --- INTEGRATIONS & GITHUB ---

class GithubConnection(Base):
    __tablename__ = "github_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    github_username: Mapped[str] = mapped_column(String(100), nullable=False)
    access_token: Mapped[str] = mapped_column(String(255), nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="github_connection")
    repositories: Mapped[List["GithubRepository"]] = relationship("GithubRepository", back_populates="connection", cascade="all, delete-orphan")


class GithubRepository(Base):
    __tablename__ = "github_repositories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_connection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("github_connections.id", ondelete="CASCADE"), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(150), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    connection: Mapped["GithubConnection"] = relationship("GithubConnection", back_populates="repositories")
    activities: Mapped[List["GithubActivity"]] = relationship("GithubActivity", back_populates="repository", cascade="all, delete-orphan")


class GithubActivity(Base):
    __tablename__ = "github_activity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("github_repositories.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False) # Commit, PR, Issue
    commit_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    activity_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    repository: Mapped["GithubRepository"] = relationship("GithubRepository", back_populates="activities")
    student: Mapped["User"] = relationship("User")


# --- EVENTS & AUDITING ---

class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="activity_events")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False) # Info, Deadline, Alert, Grade
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    reference_entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="ai_insights")


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False) # Low, Medium, High
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    recommended_intervention: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="risk_flags")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    actor: Mapped[Optional["User"]] = relationship("User")
