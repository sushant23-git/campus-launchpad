# Campus Launchpad — Production Deployment Guide

This guide details how to deploy the **Campus Launchpad** platform online. 

For a robust production environment, we split the architecture:
1. **Database**: A hosted, persistent PostgreSQL instance (via **Neon** or **Supabase**).
2. **Backend API**: A FastAPI service deployed on **Render** or **Railway**.
3. **Frontend Client**: A Next.js application deployed on **Vercel**.

---

## 1. Prerequisites
- A [GitHub](https://github.com) account.
- A [Vercel](https://vercel.com) account.
- A [Render](https://render.com) or [Railway](https://railway.app) account.
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

## 3. Step 2: Deploy the FastAPI Backend to Render
Render connects directly to your GitHub repository and redeploys automatically on git pushes.

### 3.1 Prepare Codebase for Monorepo Deployment
If your code is in a single git repository (monorepo), Render allows you to specify a **Root Directory** (`backend`).

### 3.2 Create Web Service on Render
1. Sign in to [Render](https://render.com).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository containing the Campus Launchpad project.
4. Configure the Web Service settings:
   - **Name**: `campus-launchpad-backend`
   - **Environment**: `Python`
   - **Region**: Select the closest region to your users.
   - **Branch**: `main` (or your active branch)
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free` (or higher)

### 3.3 Set Environment Variables
In the Render dashboard, navigate to **Environment** and add the following keys:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Your modified Neon/Supabase connection string |
| `JWT_SECRET_KEY` | `your-long-secure-random-string` | Generate using `openssl rand -hex 32` |
| `JWT_REFRESH_SECRET_KEY` | `another-secure-random-string` | Generate using `openssl rand -hex 32` |
| `TOTP_ISSUER` | `CampusLaunchpad` | Name shown on user 2FA screens |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | (We will update this after deploying to Vercel) |
| `AI_PROVIDER_KEY` | `mock` or `your-actual-gemini-key` | Set to `mock` if LLM service is not configured |

### 3.4 Seed the Database
Once the Render Web Service completes building and is **Live**:
1. Open Render's **Shell** tab for the Web Service.
2. Run migrations to initialize the tables:
   ```bash
   alembic upgrade head
   ```
3. Run the seeder to populate cohort parameters:
   ```bash
   python app/database/seed.py
   ```

Copy your deployed Render URL (e.g. `https://campus-launchpad-backend.onrender.com`).

---

## 4. Step 3: Deploy the Next.js Frontend to Vercel
Vercel is optimized for Next.js out-of-the-box.

### 4.1 Import Project to Vercel
1. Go to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Select your connected GitHub repository.
3. Configure the Project settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Select `frontend` (crucial for monorepos).
   - **Build & Development Settings**: Keep defaults.

### 4.2 Set Environment Variables
Expand the **Environment Variables** accordion and add:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com/api/v1` | Your deployed Render URL + `/api/v1` prefix |

4. Click **Deploy**. Vercel will compile and host your Next.js application, outputting a public URL (e.g., `https://campus-launchpad-frontend.vercel.app`).

---

## 5. Step 4: Finalize CORS Policies
1. Copy your public Vercel URL.
2. Return to the **Render Dashboard** of your backend web service.
3. Update the `CORS_ORIGINS` environment variable to include your new Vercel URL:
   ```env
   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
   ```
4. Save changes. Render will automatically redeploy the service with the new settings.

Your Campus Launchpad platform is now fully deployed and live!
- **Frontend Dashboard**: `https://your-frontend.vercel.app`
- **Backend API Docs**: `https://your-backend.onrender.com/docs`
