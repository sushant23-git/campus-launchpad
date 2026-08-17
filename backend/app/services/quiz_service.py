import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.models import Quiz, Question, QuizAttempt, QuizAnswer, Week, User, ActivityEvent
from app.schemas.schemas import QuizSubmitSchema, QuestionAnswerSchema
from app.core.exceptions import NotFoundException, BusinessRuleException, ForbiddenException
from app.services.curriculum_service import CurriculumService

class QuizService:
    @staticmethod
    async def get_available_quizzes(db: AsyncSession, student: User, week_id: Optional[uuid.UUID] = None) -> List[dict]:
        """List active quizzes checking unlock/lock constraints."""
        query = select(Quiz).filter(Quiz.is_published == True)
        if week_id:
            query = query.filter(Quiz.week_id == week_id)
            
        result = await db.execute(query)
        quizzes = result.scalars().all()
        
        quizzes_list = []
        for quiz in quizzes:
            # Check week lock state
            week_result = await db.execute(select(Week).filter(Week.id == quiz.week_id))
            week = week_result.scalar_one_or_none()
            
            is_locked = False
            lock_reason = ""
            if week:
                is_locked, lock_reason = await CurriculumService.is_week_locked_for_student(db, week, student)

            # Check attempt count
            attempt_result = await db.execute(
                select(QuizAttempt).filter(
                    QuizAttempt.quiz_id == quiz.id,
                    QuizAttempt.student_id == student.id,
                    QuizAttempt.status == "Completed"
                )
            )
            completed_attempts = len(attempt_result.scalars().all())
            attempts_remaining = max(0, quiz.attempt_limit - completed_attempts)

            quizzes_list.append({
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "week_id": quiz.week_id,
                "module_id": quiz.module_id,
                "time_limit_minutes": quiz.time_limit_minutes,
                "attempt_limit": quiz.attempt_limit,
                "passing_score": quiz.passing_score,
                "is_locked": is_locked,
                "lock_reason": lock_reason,
                "completed_attempts": completed_attempts,
                "attempts_remaining": attempts_remaining
            })
            
        return quizzes_list

    @staticmethod
    async def start_quiz_attempt(db: AsyncSession, student: User, quiz_id: uuid.UUID) -> QuizAttempt:
        """Initialize a timed quiz attempt, verifying limits and locks."""
        # Fetch quiz
        result = await db.execute(
            select(Quiz)
            .filter(Quiz.id == quiz_id, Quiz.is_published == True)
            .options(selectinload(Quiz.questions))
        )
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise NotFoundException("Quiz could not be found.")

        # Check lock state
        week_result = await db.execute(select(Week).filter(Week.id == quiz.week_id))
        week = week_result.scalar_one_or_none()
        if week:
            is_locked, lock_reason = await CurriculumService.is_week_locked_for_student(db, week, student)
            if is_locked:
                raise ForbiddenException(f"Quiz is locked: {lock_reason}")

        # Check attempt limits
        attempt_result = await db.execute(
            select(QuizAttempt).filter(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.student_id == student.id,
                QuizAttempt.status == "Completed"
            )
        )
        completed_attempts = len(attempt_result.scalars().all())
        if completed_attempts >= quiz.attempt_limit:
            raise BusinessRuleException("Maximum attempt limit reached for this quiz.")

        # Check if there's already an active In_Progress attempt
        active_attempt_res = await db.execute(
            select(QuizAttempt).filter(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.student_id == student.id,
                QuizAttempt.status == "In_Progress"
            )
        )
        active_attempt = active_attempt_res.scalar_one_or_none()
        
        if active_attempt:
            # Check if it has expired
            expiry_time = active_attempt.started_at + timedelta(minutes=quiz.time_limit_minutes)
            if datetime.utcnow() > expiry_time:
                # Mark as completed/failed due to timeout
                active_attempt.status = "Completed"
                active_attempt.submitted_at = expiry_time
                await db.commit()
            else:
                return active_attempt

        # Create new attempt
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            student_id=student.id,
            started_at=datetime.utcnow(),
            status="In_Progress",
            score=0.0
        )
        db.add(attempt)
        
        # Log Activity Event
        event = ActivityEvent(
            user_id=student.id,
            event_type="QUIZ_STARTED",
            entity_type="QuizAttempt",
            entity_id=attempt.id,
            payload={"quiz_id": str(quiz.id)}
        )
        db.add(event)
        
        await db.commit()
        await db.refresh(attempt)
        return attempt

    @staticmethod
    async def save_intermediate_answers(
        db: AsyncSession,
        student: User,
        attempt_id: uuid.UUID,
        answers: List[QuestionAnswerSchema]
    ) -> None:
        """Autosave intermediate student answers locally and in DB before submission."""
        result = await db.execute(
            select(QuizAttempt)
            .filter(QuizAttempt.id == attempt_id, QuizAttempt.student_id == student.id)
            .options(selectinload(QuizAttempt.quiz))
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise NotFoundException("Quiz attempt not found.")
            
        if attempt.status != "In_Progress":
            raise BusinessRuleException("Cannot save answers. Quiz attempt is not active.")

        # Verify time limit has not expired
        expiry_time = attempt.started_at + timedelta(minutes=attempt.quiz.time_limit_minutes)
        if datetime.utcnow() > expiry_time:
            attempt.status = "Completed"
            attempt.submitted_at = expiry_time
            await db.commit()
            raise BusinessRuleException("Quiz time limit has expired.")

        # Save answers
        for ans in answers:
            # Check existing answer
            ans_res = await db.execute(
                select(QuizAnswer).filter(
                    QuizAnswer.attempt_id == attempt_id,
                    QuizAnswer.question_id == ans.question_id
                )
            )
            db_ans = ans_res.scalar_one_or_none()

            if not db_ans:
                db_ans = QuizAnswer(
                    attempt_id=attempt_id,
                    question_id=ans.question_id,
                    selected_options={"selections": ans.selected_options},
                    is_correct=False,
                    marks_awarded=0.0
                )
                db.add(db_ans)
            else:
                db_ans.selected_options = {"selections": ans.selected_options}

        await db.commit()

    @staticmethod
    async def submit_quiz_attempt(
        db: AsyncSession,
        student: User,
        schema: QuizSubmitSchema
    ) -> QuizAttempt:
        """Process quiz submission and automatically grade objective questions."""
        result = await db.execute(
            select(QuizAttempt)
            .filter(QuizAttempt.id == schema.attempt_id, QuizAttempt.student_id == student.id)
            .options(
                selectinload(QuizAttempt.quiz)
                .selectinload(Quiz.questions)
            )
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise NotFoundException("Quiz attempt not found.")

        if attempt.status != "In_Progress":
            raise BusinessRuleException("Attempt has already been submitted or completed.")

        # Check timeout (with 30s network buffer)
        expiry_time = attempt.started_at + timedelta(minutes=attempt.quiz.time_limit_minutes) + timedelta(seconds=30)
        submitted_at = datetime.utcnow()
        if submitted_at > expiry_time:
            # Overdue submission
            submitted_at = attempt.started_at + timedelta(minutes=attempt.quiz.time_limit_minutes)

        # First, save any final answers sent during submission
        await QuizService.save_intermediate_answers(db, student, schema.attempt_id, schema.answers)

        # Grade attempt
        total_marks = 0.0
        max_marks = 0.0
        
        # Load all answers saved for this attempt
        ans_res = await db.execute(
            select(QuizAnswer).filter(QuizAnswer.attempt_id == attempt.id)
        )
        saved_answers = {ans.question_id: ans for ans in ans_res.scalars().all()}

        for question in attempt.quiz.questions:
            max_marks += question.marks
            answer = saved_answers.get(question.id)
            if not answer:
                # Student did not answer this question
                continue
            
            selections = answer.selected_options.get("selections", [])
            correct_keys = question.correct_answer.get("answers", [])
            
            # Simple grading logic depending on type
            is_correct = False
            marks_awarded = 0.0
            
            if question.question_type in ["MCQ", "TF"]:
                if len(selections) == 1 and len(correct_keys) == 1:
                    is_correct = (selections[0].strip().lower() == correct_keys[0].strip().lower())
            elif question.question_type == "MSQ":
                # Compare lists (order independent)
                is_correct = (sorted([s.strip().lower() for s in selections]) == 
                              sorted([c.strip().lower() for c in correct_keys]))
            elif question.question_type == "Short_Answer":
                if len(selections) == 1 and len(correct_keys) == 1:
                    is_correct = (selections[0].strip().lower() == correct_keys[0].strip().lower())
            elif question.question_type == "Long_Answer":
                # Essay questions require manual review from mentor; default to False
                is_correct = False
                
            if is_correct:
                marks_awarded = question.marks
                
            answer.is_correct = is_correct
            answer.marks_awarded = marks_awarded
            total_marks += marks_awarded

        # Calculate percentage score
        score_percent = (total_marks / max_marks * 100.0) if max_marks > 0 else 0.0

        # Update attempt fields
        attempt.status = "Completed"
        attempt.submitted_at = submitted_at
        attempt.score = score_percent

        # Log Activity Event
        event = ActivityEvent(
            user_id=student.id,
            event_type="QUIZ_COMPLETED",
            entity_type="QuizAttempt",
            entity_id=attempt.id,
            payload={"score": score_percent, "passed": score_percent >= attempt.quiz.passing_score}
        )
        db.add(event)

        await db.commit()
        await db.refresh(attempt)
        return attempt
