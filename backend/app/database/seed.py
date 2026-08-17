import asyncio
import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.models import Week, Module, Task, Quiz, Question, Domain, Cohort, User, UserProfile
from app.core.security import get_password_hash

async def seed_data(db: AsyncSession):
    # 1. Seed Cohort
    cohort = Cohort(
        id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        name="Inaugural Cohort 2026",
        batch_year=2026,
        max_students=250,
        start_date=date.today() - timedelta(days=14),
        end_date=date.today() + timedelta(days=70),
        is_active=True
    )
    db.add(cohort)
    await db.flush()

    # Seed default users
    admin_user = User(
        id=uuid.UUID("11111111-1111-1111-1111-11111111111a"),
        email="admin@campuslaunchpad.com",
        password_hash=get_password_hash("AdminDevelopment123!"),
        role="admin",
        is_active=True,
        is_verified=True
    )
    mentor_user = User(
        id=uuid.UUID("22222222-2222-2222-2222-22222222222b"),
        email="mentor@campuslaunchpad.com",
        password_hash=get_password_hash("MentorDevelopment123!"),
        role="mentor",
        is_active=True,
        is_verified=True
    )
    student_user = User(
        id=uuid.UUID("33333333-3333-3333-3333-33333333333c"),
        email="student1@campuslaunchpad.com",
        password_hash=get_password_hash("StudentDevelopment123!"),
        role="student",
        is_active=True,
        is_verified=True
    )
    db.add(admin_user)
    db.add(mentor_user)
    db.add(student_user)
    await db.flush()

    # Seed student profile
    student_profile = UserProfile(
        id=uuid.UUID("44444444-4444-4444-4444-44444444444d"),
        user_id=student_user.id,
        full_name="Alice Student",
        college_name="State Tech University",
        branch="Computer Science",
        year=1,
        xp=0,
        level=1,
        profile_completed=True
    )
    db.add(student_profile)
    await db.flush()

    # 2. Seed Technical Domains
    domains = [
        Domain(
            id=uuid.uuid4(),
            name="Software Engineering",
            description="Core language paradigms, data structures, algorithms, and modular design.",
            beginner_learning_activity="Read systems engineering tutorials and complete CLI module setups.",
            mini_challenge="Solve a basic binary tree inversion logic puzzle on GitHub."
        ),
        Domain(
            id=uuid.uuid4(),
            name="Web Development",
            description="Full-stack web applications, frontends, APIs, backends, and caching layers.",
            beginner_learning_activity="Read REST API and HTTP status protocols guides.",
            mini_challenge="Create a simplified FastAPI CRUD backend service."
        ),
        Domain(
            id=uuid.uuid4(),
            name="Artificial Intelligence & ML",
            description="Regression models, classifications, deep learning neural networks, and prompt engineering.",
            beginner_learning_activity="Read linear algebra basics and statistical classification tutorials.",
            mini_challenge="Build a basic Scikit-learn regression model for prediction."
        ),
        Domain(
            id=uuid.uuid4(),
            name="Cybersecurity",
            description="Network protocols, vulnerability audits, encryption schemes, and secure auth layers.",
            beginner_learning_activity="Read network handshakes and cryptography protocols specs.",
            mini_challenge="Audit a sample API node for JWT signing vulnerability."
        ),
        Domain(
            id=uuid.uuid4(),
            name="Robotics & IoT",
            description="Embedded firmware controllers, sensory feedback loops, serial communications, and kinematics.",
            beginner_learning_activity="Read microcontrollers specs and GPIO serial buses guides.",
            mini_challenge="Write a basic C++ script to read simulated sensory data."
        )
    ]
    for d in domains:
        db.add(d)
    await db.flush()

    # 3. Seed 12 Weeks of Curriculum
    weeks_data = [
        {"week": 1, "title": "Onboarding & Fundamentals", "description": "Syllabus foundations, workspace setups, and git basics.", "days": -14},
        {"week": 2, "title": "Git Basics & Declarative Schemas", "description": "Database relational models, schemas, and constraints.", "days": -7},
        {"week": 3, "title": "Secure Authentication Layers", "description": "JSON Web Token setups, passwords hashing, and middleware filters.", "days": 0},
        {"week": 4, "title": "Module CRUD Actions & Roadmaps", "description": "Building weeks, modules and tasks CRUD API endpoints.", "days": 7},
        {"week": 5, "title": "Domain Specialization Exploration", "description": "Specializing in software, web, AI/ML, cyber, or IoT systems.", "days": 14},
        {"week": 6, "title": "Collaborative Team Workflows", "description": "Reciprocal peer code evaluations and collaboration verification.", "days": 21},
        {"week": 7, "title": "Milestone Design Architectures", "description": "Industry project team creation and milestone deliverables.", "days": 28},
        {"week": 8, "title": "Auditing and System Logs", "description": "Auditable event logging trails and analytics compiles.", "days": 35},
        {"week": 9, "title": "AI Analytics and Predictions", "description": "Performance insights compiles grounded in db metrics.", "days": 42},
        {"week": 10, "title": "CSV Exports and Data Backups", "description": "Generating streaming CSV files for administrative audit reports.", "days": 49},
        {"week": 11, "title": "Performance Optimization & Scaling", "description": "Database indexing optimization and cache controls.", "days": 56},
        {"week": 12, "title": "Final Milestone Presentation Showcase", "description": "Presenting working systems to cohort mentors.", "days": 63}
    ]

    weeks = []
    for wd in weeks_data:
        w = Week(
            id=uuid.uuid4(),
            week_number=wd["week"],
            title=wd["title"],
            description=wd["description"],
            start_date=date.today() + timedelta(days=wd["days"]),
            end_date=date.today() + timedelta(days=wd["days"] + 6),
            unlock_at=datetime.utcnow() + timedelta(days=wd["days"]),
            is_published=True
        )
        db.add(w)
        weeks.append(w)
    await db.flush()

    # 4. Seed Modules for Week 1
    w1 = weeks[0]
    m1 = Module(
        id=uuid.uuid4(),
        week_id=w1.id,
        title="Welcome to Campus Launchpad",
        description="Campus Launchpad is a 12-week development intensive. Over the next weeks, you will build full-stack architectures, run tests, form balanced teams, and integrate analytics.",
        estimated_minutes=5,
        sequence=1
    )
    m2 = Module(
        id=uuid.uuid4(),
        week_id=w1.id,
        title="Foundations of Computer Systems",
        description="Explore core terminal shells, package dependency managers, runtime compilers, and git workflows. These foundations are crucial for developer productivity.",
        estimated_minutes=8,
        sequence=2
    )
    db.add(m1)
    db.add(m2)
    await db.flush()

    # 5. Seed Tasks for Week 1
    t1 = Task(
        id=uuid.uuid4(),
        week_id=w1.id,
        module_id=m1.id,
        title="Setup Your Developer Workspace",
        description="Verify your programming environment. Fork the monorepo scaffold, complete onboarding settings, and push your first git commit.",
        category="General",
        difficulty="Easy",
        is_mandatory=True,
        xp_reward=100,
        deadline=datetime.utcnow() + timedelta(days=5),
        estimated_time_minutes=45,
        submission_type="Text",
        evaluation_method="Manual",
        sequence=1,
        is_published=True
    )
    db.add(t1)
    await db.flush()

    # 6. Seed Quiz for Week 1
    qz = Quiz(
        id=uuid.uuid4(),
        week_id=w1.id,
        module_id=m1.id,
        title="Week 1 Foundations Checkpoint",
        description="timed evaluation verifying terminal commands, git basics, and package settings.",
        time_limit_minutes=15,
        attempt_limit=3,
        passing_score=75.0,
        is_published=True
    )
    db.add(qz)
    await db.flush()

    # Questions for Week 1 Quiz
    qn1 = Question(
        id=uuid.uuid4(),
        quiz_id=qz.id,
        question_type="MCQ",
        question_text="Which git command initializes a repository locally?",
        options=["git clone", "git init", "git start", "git setup"],
        correct_answer={"answers": ["git init"]},
        marks=5.0,
        sequence=1
    )
    qn2 = Question(
        id=uuid.uuid4(),
        quiz_id=qz.id,
        question_type="MSQ",
        question_text="Select all features supported in Campus Launchpad.",
        options=["XP double-entry ledger", "Unlock check overrides", "AI progress predictions", "Automated MCQ grading"],
        correct_answer={"answers": ["XP double-entry ledger", "Unlock check overrides", "AI progress predictions", "Automated MCQ grading"]},
        marks=10.0,
        sequence=2
    )
    db.add(qn1)
    db.add(qn2)

    await db.commit()
    print("Database successfully seeded with foundational cohort records!")

if __name__ == "__main__":
    async def main():
        from app.database.session import engine
        from app.database.base_model import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        async with AsyncSessionLocal() as session:
            await seed_data(session)
    asyncio.run(main())
