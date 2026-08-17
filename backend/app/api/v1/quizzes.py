from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Optional
import uuid
from pydantic import BaseModel

from app.database.session import get_db
from app.api.v1.deps import get_current_user, check_role
from app.services.quiz_service import QuizService
from app.schemas.schemas import (
    APIResponse, QuizResponse, QuizAttemptResponse, QuizSubmitSchema,
    QuestionAnswerSchema, QuestionResponse
)
from app.models.models import User, QuizAttempt, Question, QuizAnswer
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

router = APIRouter()

class SaveAnswersRequest(BaseModel):
    answers: List[QuestionAnswerSchema]

@router.get("", response_model=APIResponse[List[Any]])
async def get_quizzes(
    week_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve all available quizzes with attempts constraints."""
    quizzes = await QuizService.get_available_quizzes(db, current_user, week_id)
    return APIResponse(success=True, data=quizzes)

@router.post("/{quiz_id}/start", response_model=APIResponse[Any])
async def start_quiz(
    quiz_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Initialize a timed quiz attempt."""
    attempt = await QuizService.start_quiz_attempt(db, current_user, quiz_id)
    # Fetch questions for this quiz to present to the user
    q_result = await db.execute(
        select(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.sequence)
    )
    questions = q_result.scalars().all()
    
    questions_resp = [QuestionResponse.from_orm(q) for q in questions]
    attempt_resp = QuizAttemptResponse.from_orm(attempt)

    data = {
        "attempt": attempt_resp,
        "questions": questions_resp
    }
    return APIResponse(success=True, data=data, message="Quiz attempt started.")

@router.post("/attempts/{attempt_id}/save", response_model=APIResponse[None])
async def save_answers(
    attempt_id: uuid.UUID,
    body: SaveAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Autosave intermediate student answers periodically during the attempt."""
    await QuizService.save_intermediate_answers(db, current_user, attempt_id, body.answers)
    return APIResponse(success=True, data=None, message="Answers autosaved.")

@router.post("/attempts/submit", response_model=APIResponse[Any])
async def submit_quiz(
    body: QuizSubmitSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Submit quiz and triggers automatic grading engine."""
    attempt = await QuizService.submit_quiz_attempt(db, current_user, body)
    resp = QuizAttemptResponse.from_orm(attempt)
    return APIResponse(success=True, data=resp, message="Quiz submitted and graded.")

@router.get("/attempts/{attempt_id}", response_model=APIResponse[Any])
async def get_attempt_details(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch completed quiz attempt results, questions, and correct answers."""
    result = await db.execute(
        select(QuizAttempt)
        .filter(QuizAttempt.id == attempt_id)
        .options(selectinload(QuizAttempt.quiz))
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        return APIResponse(success=False, data=None, message="Attempt not found.")
        
    # Security: student can only view their own attempts, unless they are admin or mentor
    if attempt.student_id != current_user.id and current_user.role not in ["mentor", "admin"]:
        return APIResponse(success=False, data=None, message="Unauthorized access.")

    # Load questions and answers
    q_result = await db.execute(
        select(Question)
        .filter(Question.quiz_id == attempt.quiz_id)
        .order_by(Question.sequence)
    )
    questions = q_result.scalars().all()

    ans_result = await db.execute(
        select(QuizAnswer).filter(QuizAnswer.attempt_id == attempt_id)
    )
    answers = ans_result.scalars().all()
    answers_map = {ans.question_id: ans for ans in answers}

    questions_data = []
    for q in questions:
        ans = answers_map.get(q.id)
        selected = ans.selected_options.get("selections", []) if ans else []
        is_correct = ans.is_correct if ans else False
        marks_awarded = ans.marks_awarded if ans else 0.0

        questions_data.append({
            "id": q.id,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "options": q.options,
            "marks": q.marks,
            "sequence": q.sequence,
            "selected_options": selected,
            "is_correct": is_correct,
            "marks_awarded": marks_awarded,
            "correct_answer": q.correct_answer.get("answers", []) # expose correct answers for review
        })

    data = {
        "attempt": QuizAttemptResponse.from_orm(attempt),
        "quiz_title": attempt.quiz.title,
        "questions": questions_data
    }
    return APIResponse(success=True, data=data)
