# TechStack.md

## Frontend

-   Next.js 15
-   React 19
-   TypeScript
-   Tailwind CSS
-   shadcn/ui
-   Framer Motion
-   PWA Support

## Backend

-   FastAPI
-   SQLAlchemy
-   Alembic
-   Pydantic

## Database

-   PostgreSQL

## Cache and Background Jobs

-   Redis
-   APScheduler

## Browser Automation

-   Playwright

## Authentication

-   JWT Authentication
-   Google OAuth

## AI Layer

IMPORTANT: Use the Groq API for all LLM operations.

Environment Variable: GROQ_API_KEY=`<user_groq_api_key>`{=html}

Recommended Models: - openai/gpt-oss-120b - llama-3.3-70b-versatile -
deepseek-r1-distill-llama-70b

Use Groq for: - Resume Parsing - Job Matching - Skill Extraction - Cover
Letter Generation - Email Classification - Recommendation Engine

Do NOT use OpenAI APIs unless explicitly configured by the user.

## Email Integration

-   Gmail OAuth
-   Gmail API

## Storage

-   Local storage for development
-   S3 compatible storage for production

## Deployment

-   Docker
-   Docker Compose
-   Single VPS deployment
