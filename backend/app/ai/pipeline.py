import uuid
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import ProgressMetrics, UserProfile, User, AIInsight
from app.core.config import settings

class AIPipeline:
    @staticmethod
    async def generate_student_insights(
        db: AsyncSession,
        student_id: uuid.UUID,
        week_number: int
    ) -> AIInsight:
        """Analyze weekly student progress metrics and save personalized AI insights."""
        # 1. Fetch latest progress metrics
        prog_res = await db.execute(
            select(ProgressMetrics).filter(
                ProgressMetrics.student_id == student_id,
                ProgressMetrics.week_number == week_number
            )
        )
        metrics = prog_res.scalar_one_or_none()
        
        # Load user profile
        profile_res = await db.execute(
            select(UserProfile).filter(UserProfile.user_id == student_id)
        )
        profile = profile_res.scalar_one_or_none()
        
        # Default fallback if data is missing
        if not metrics or not profile:
            insight = AIInsight(
                student_id=student_id,
                insight_type="Weekly Progress Support",
                summary="You are at the start of your engineering roadmap. Continue reading curriculum modules!",
                recommendation="Explore your onboarding modules and connect with your peer group teammates to get started.",
                confidence=1.0,
                generated_at=datetime.utcnow()
            )
            db.add(insight)
            await db.commit()
            return insight

        # 2. Grounded deterministic rules (ensuring AI does not fabricate student activities)
        summary_items = []
        rec_items = []

        # Analyze task submissions
        if metrics.task_score >= 90.0:
            summary_items.append(f"Outstanding task completion this week ({metrics.task_score:.1f}%).")
            rec_items.append("Keep up this excellent pace. Consider attempting optional challenges for extra XP.")
        elif metrics.task_score >= 60.0:
            summary_items.append(f"Steady progress on weekly assignments ({metrics.task_score:.1f}%), but you have missing mandatory tasks.")
            rec_items.append("Focus on resolving pending tasks in your backlog before the week lock date.")
        else:
            summary_items.append(f"Task completion rate is trailing significantly ({metrics.task_score:.1f}%).")
            rec_items.append("Prioritize core mandatory tasks to catch up with the curriculum schedule.")

        # Analyze quiz performance
        if metrics.assessment_score >= 80.0:
            summary_items.append(f"Strong understanding of concepts shown on your assessments ({metrics.assessment_score:.1f}%).")
        elif metrics.assessment_score >= 50.0:
            summary_items.append(f"Moderate quiz scores ({metrics.assessment_score:.1f}%). Concept gaps exist.")
            rec_items.append("Review weekly readings and sample code blocks before retaking assessments.")
        else:
            summary_items.append(f"Concept assessment scores are currently low ({metrics.assessment_score:.1f}%).")
            rec_items.append("Review module materials carefully or check in with your mentor for support.")

        # Analyze streaks
        if profile.current_streak >= 5:
            summary_items.append(f"Great consistency! You have maintained a check-in streak of {profile.current_streak} days.")
            rec_items.append("Protect your daily active learning streak to earn streak bonuses.")

        summary_text = " ".join(summary_items)
        recommendation_text = " ".join(rec_items)

        # 3. AI Refinement (Dual-mode, safe fallback)
        if settings.AI_PROVIDER_KEY != "mock" and settings.AI_PROVIDER_KEY != "":
            try:
                # LLM API configuration
                prompt = (
                    "Refine this educational coach summary and recommendation to be highly motivating and direct. "
                    "Do not fabricate any scores or data. Keep it concise (under 2 sentences per section).\n\n"
                    f"Stats:\n- Tasks: {metrics.task_score}%\n- Quizzes: {metrics.assessment_score}%\n- Streak: {profile.current_streak} days\n\n"
                    f"Summary: {summary_text}\n"
                    f"Recommendation: {recommendation_text}"
                )
                
                # Standard HTTP request (Gemini example)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL_NAME}:generateContent?key={settings.AI_PROVIDER_KEY}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=data, timeout=8.0)
                    if response.status_code == 200:
                        raw_resp = response.json()
                        refined_text = raw_resp["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # Parse the text into summary and recommendation if needed
                        # Or simply split by paragraphs. Here we set it as refined summary.
                        summary_text = refined_text.strip()
            except Exception:
                # Degrades gracefully to templates if LLM service is offline or throws error
                pass

        # 4. Save to DB
        insight = AIInsight(
            student_id=student_id,
            insight_type="Weekly Progress Insights",
            summary=summary_text,
            recommendation=recommendation_text,
            confidence=0.9,
            generated_at=datetime.utcnow()
        )
        db.add(insight)
        await db.commit()
        return insight
