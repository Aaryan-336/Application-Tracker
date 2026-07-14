# Deployment Guide: Render (Backend) + Vercel (Frontend)

This guide walks you through deploying the **AI Career Agent** to production.

---

## Part 1: Deploy Backend to Render

Render will host your FastAPI application and your PostgreSQL database.

### 1. Provision a PostgreSQL Database
1. Go to your [Render Dashboard](https://render.com/) and click **New → PostgreSQL**.
2. Set the following details:
   - **Name**: `applications-tracker-db`
   - **Database**: `applications_tracker`
   - **User**: `db_user`
   - **Region**: Choose one closest to you (e.g., `Oregon (US West)` or `Frankfurt (EU Central)`)
3. Click **Create Database**.
4. Once created, copy the **Internal Database URL** (for other Render services) or **External Database URL**.

### 2. Create the FastAPI Web Service
1. Click **New → Web Service**.
2. Connect your GitHub/GitLab repository.
3. Configure the service:
   - **Name**: `applications-tracker-backend`
   - **Environment**: `Python`
   - **Region**: (Same region as your database!)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Expand the **Advanced** section and add the following **Environment Variables**:

| Key | Value | Description |
|---|---|---|
| `DATABASE_URL` | *[Your Render Internal Database URL]* | Points to the postgres DB |
| `JWT_SECRET_KEY` | *[Generate a long random string]* | e.g. run `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token expiration (7 days) |
| `GROQ_API_KEY` | *[Your Groq API Key]* | Required for AI Resume matching |
| `JSEARCH_API_KEY` | *[Your JSearch RapidAPI Key]* | (Optional) For jobs API |
| `ADZUNA_APP_ID` | *[Your Adzuna App ID]* | (Optional) For jobs API |
| `ADZUNA_APP_KEY` | *[Your Adzuna App Key]* | (Optional) For jobs API |

5. Click **Create Web Service**.
6. Render will build and deploy your backend. Once complete, copy your backend's live URL (e.g., `https://applications-tracker-backend.onrender.com`).

---

## Part 2: Deploy Frontend to Vercel

Vercel will build and host your Next.js frontend application.

### 1. Import Project to Vercel
1. Go to your [Vercel Dashboard](https://vercel.com/) and click **Add New → Project**.
2. Select your git repository.
3. In the project setup panel:
   - **Framework Preset**: Vercel will auto-detect **Next.js**.
   - **Root Directory**: `frontend` (Ensure you set this to the `frontend` folder!)
4. Expand the **Environment Variables** section and add:

| Key | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://[your-backend-app].onrender.com/api` | **Must end with `/api`** |

5. Click **Deploy**.

---

## Checklist: Verify Production Setup
- [ ] Log in to your live Vercel app.
- [ ] Register a new account.
- [ ] Go to Profile and upload a resume (checks connection to backend and database).
- [ ] Run job discovery (checks API-based job fetching).
- [ ] Connect Gmail using an App Password (checks SSL IMAP connection).
