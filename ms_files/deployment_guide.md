# Campus Launchpad — Production Deployment Guide

This guide details how to deploy the **Campus Launchpad** platform online.

We support two deployment options:
1. **Option A: Vercel Unified Monorepo (Easiest & 100% Free)**: Deploys both the Next.js frontend and the FastAPI backend to the same Vercel project using Vercel Serverless Functions.
2. **Option B: Split Deployment**: Deploys the Next.js frontend to Vercel and the FastAPI backend as a persistent service on Render or Railway.

Both options connect to a hosted production PostgreSQL instance (such as **Neon** or **Supabase**).

---

## 1. Prerequisites
- A [GitHub](https://github.com) account.
- A [Vercel](https://vercel.com) account.
- A [Neon](https://neon.tech) or [Supabase](https://supabase.com) account (for hosted PostgreSQL).

---

## 2. Step 1: Provision a Hosted PostgreSQL Database
SQLite files are local and ephemeral. When deploying to serverless platforms, your files are wiped on redeployment. 

### Using Neon (Recommended)
1. Go to [Neon.tech](https://neon.tech) and sign up.
2. Create a new project named `campus-launchpad`.
3. Select your region and choose **PostgreSQL 16**.
4. In the Neon Console, copy your **Connection String** (use the pooled connection string ending with `?sslmode=require`). It will look like this:
   ```env
   postgresql://alex:password@ep-cool-wave-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. Modify the connection protocol prefix from `postgresql://` to `postgresql+asyncpg://` for SQLAlchemy's async driver:
   ```env
   postgresql+asyncpg://alex:password@ep-cool-wave-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

---

## 3. Option A: Unified Monorepo Deployment on Vercel (Easiest)

By using the provided `vercel.json` in the root of the project, Vercel will build both the Next.js client and the Python Serverless API function under the same domain.

### 3.1 Setup Vercel Project
1. Open the [Vercel Dashboard](https://vercel.com) and click **Add New > Project**.
2. Select your connected GitHub repository.
3. Keep the **Root Directory** as the repository root (do **NOT** change it to `frontend`).
4. Vercel will automatically detect `vercel.json` and configure the build pipelines for both Next.js and Python.

### 3.2 Set Environment Variables
In the Vercel dashboard project settings, add the following variables under **Environment Variables**:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Your Neon/Supabase database connection string |
| `JWT_SECRET_KEY` | `your-secure-random-key` | Generate using `openssl rand -hex 32` |
| `JWT_REFRESH_SECRET_KEY` | `another-secure-random-key` | Generate using `openssl rand -hex 32` |
| `TOTP_ISSUER` | `CampusLaunchpad` | Issuer name for Google Authenticator |
| `NEXT_PUBLIC_API_URL` | `/api/v1` | **Relative URL path** (allows frontend and backend to communicate natively under the same domain) |
| `AI_PROVIDER_KEY` | `mock` or your key | Set to `mock` if AI modules are bypassed |

5. Click **Deploy**. Vercel will build the frontend, package the python dependencies, and expose your platform live (e.g. `https://campus-launchpad.vercel.app`).

---

## 4. Option B: Split Deployment (Vercel Frontend + Render Backend)

If you prefer to run FastAPI as a persistent background process (e.g., to handle long-running transactions or WebSocket streams without serverless timeouts):

### 4.1 Deploy Backend to Render
1. Sign in to [Render](https://render.com).
2. Click **New +** and select **Web Service**.
3. Connect your repository.
4. Configure service settings:
   - **Name**: `campus-launchpad-backend`
   - **Environment**: `Python`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment**, add:
   - `DATABASE_URL` (Neon Postgres url)
   - `JWT_SECRET_KEY` & `JWT_REFRESH_SECRET_KEY`
   - `CORS_ORIGINS`: Set to your deployed Vercel URL (e.g. `https://campus-launchpad.vercel.app`)

### 4.2 Deploy Frontend to Vercel
1. Create a project in Vercel.
2. Select your repository, and set **Root Directory** to `frontend`.
3. Add the environment variable:
   - `NEXT_PUBLIC_API_URL`: `https://campus-launchpad-backend.onrender.com/api/v1`
4. Deploy the project.

---

## 5. Running Database Migrations & Seeding in Production

To populate your live PostgreSQL database with cohorts, weekly timelines, domains, and timed quiz checkpoint questions:

1. Open your terminal locally on your machine.
2. Ensure you have the `DATABASE_URL` pointing to your production database in your local `.env` file (temporarily, or pass it directly in the command line).
3. Execute Alembic migrations to construct the database schema on your hosted database:
   ```bash
   $env:DATABASE_URL="postgresql+asyncpg://..."; $env:PYTHONPATH="backend"; uv run alembic upgrade head
   ```
4. Execute the seeder script to populate default data:
   ```bash
   $env:DATABASE_URL="postgresql+asyncpg://..."; $env:PYTHONPATH="backend"; uv run python backend/app/database/seed.py
   ```
