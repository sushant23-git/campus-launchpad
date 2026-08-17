# Campus Launchpad

A comprehensive 12-week student-led technical development, exploration, collaboration, assessment, and project platform designed for cohort-based student development.

---

## 1. Project Overview

Campus Launchpad is a modular full-stack platform built to transition students from foundational concepts to real-world software and hardware engineering. The platform guides students through structured steps: **Explore → Learn → Practice → Collaborate → Build → Measure → Reflect → Improve**.

It provides:
- A dynamic, database-driven 12-week curriculum.
- Secure Role-Based Access Control (RBAC) supporting **Students, Mentors, and Admins**.
- Multi-device sessions and administrative TOTP-based 2FA.
- Version-controlled submission systems, quizzes with autosave, and deterministic scoring engines (XP, Progress, Streak, Ranking).
- Sandbox execution for coding challenges and GitHub sync integrations.
- An analytics and AI insight layer based on durable database metrics.

---

## 2. Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React 18, TypeScript | Modular component-based client interface |
| **UI Styling** | Tailwind CSS | Utility-first responsive design framework |
| **Backend API**| FastAPI, Python 3.11/3.12 | Async REST API framework with native OpenAPI docs |
| **Database** | PostgreSQL 16 | Relational persistent store |
| **ORM** | SQLAlchemy 2.0 (Asyncio) | Database access and transaction mapping |
| **Cache/Queue**| Redis 7 | Caching, rate-limiting, and Celery tasks broker |
| **Containers** | Docker, Docker Compose | Service encapsulation and orchestration |
| **Testing** | Pytest, Pytest-Asyncio | Automated backend and integration tests |

---

## 3. Directory Structure

```text
campus-launchpad/
├── backend/                  # FastAPI Application
│   ├── alembic/              # DB Migrations configuration & history
│   ├── app/
│   │   ├── api/v1/           # API Routers
│   │   ├── core/             # Settings, security, storage
│   │   ├── database/         # Session setup & base model
│   │   ├── engines/          # Scopes: XP, progress, ranking, risk
│   │   ├── models/           # Declarative DB Tables
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── services/         # Handlers & controller business logic
│   └── tests/                # Unit & integration test suites
├── frontend/                 # Next.js Application
│   ├── app/                  # Next.js App Router folders
│   ├── components/           # UI primitives (Buttons, Cards, Inputs)
│   ├── features/             # Feature-specific sub-components
│   └── services/             # Axios API wrapper functions
├── docs/                     # Technical specifications & system logs
├── docker-compose.yml        # Multi-container dev runner
├── .env.example              # Environment blueprint
└── README.md                 # Root documentation
```

---

## 4. Prerequisites

To run this platform locally, make sure you have installed:
- [Docker & Docker Compose](https://www.docker.com/products/docker-desktop)
- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)

---

## 5. Installation & Setup

### Step 1: Clone and Configure Environment
Copy the blueprint configuration and rename it:
```bash
cp .env.example .env
```
*(Update default credentials in `.env` if necessary; they default to pre-configured Docker service values).*

### Step 2: Spin Up Containers
Use docker-compose to orchestrate and run all services:
```bash
docker compose up --build
```
This launches:
- **PostgreSQL (`db`)** on port `5432`
- **Redis (`cache`)** on port `6379`
- **FastAPI Backend (`backend`)** on port `8000` (docs available at [http://localhost:8000/docs](http://localhost:8000/docs))
- **NextJS Frontend (`frontend`)** on port `3000`

### Step 3: Run Database Migrations
Enter the backend container and apply Alembic migrations:
```bash
docker compose exec backend alembic upgrade head
```

### Step 4: Seed Initial Data
Create sample accounts, 12 weeks of curriculum, peer groups, and tasks:
```bash
docker compose exec backend python scripts/seed.py
```
**Development Login Credentials:**
*   **Admin:** `admin@campuslaunchpad.com` / `AdminDevelopment123!`
*   **Mentor:** `mentor@campuslaunchpad.com` / `MentorDevelopment123!`
*   **Student:** `student1@campuslaunchpad.com` / `StudentDevelopment123!`

---

## 6. Running Tests

We run tests via pytest inside the backend container.

### Run All Tests
```bash
docker compose exec backend pytest
```

### Run Specific Test Modules
```bash
docker compose exec backend pytest tests/unit/test_xp_engine.py
docker compose exec backend pytest tests/integration/test_auth.py
```

---

## 7. Troubleshooting

- **Redis Connection Failures:** Verify that the `cache` container is healthy using `docker compose ps`. Restart if stuck.
- **PostgreSQL Authentication Errors:** Ensure the connection string in your `.env` matches the configuration details of the PostgreSQL environment variables.
- **Port Conflict:** If ports `5432`, `6379`, `8000`, or `3000` are already bound to local background services, modify host mappings inside `docker-compose.yml`.

---

## 8. Contribution Guidelines

1. **Create a Feature Branch:** Do not push modifications directly to `main` or `develop`.
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Write Unit/Integration Tests:** Update test suites to cover calculation logic or API changes.
3. **Run Checks:** Verify code format, linting, and run test suites before creating a pull request.
