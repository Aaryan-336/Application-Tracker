import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, resume, jobs, applications, gmail
from app.services.scheduler import start_scheduler, shutdown_scheduler

# Create tables on startup (as a backup to init_db.py)
Base.metadata.create_all(bind=engine)

# Inline database migration for gmail and experience columns
from sqlalchemy import text
try:
    with engine.connect() as conn:
        res = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='gmail_address'"
        ))
        if not res.fetchone():
            print("Running inline database migration to add gmail fields to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN gmail_address VARCHAR(255) NULL"))
            conn.execute(text("ALTER TABLE users ADD COLUMN gmail_app_password VARCHAR(255) NULL"))
            conn.execute(text("ALTER TABLE users ADD COLUMN gmail_last_synced TIMESTAMP NULL"))
            conn.commit()
            print("Gmail migration completed.")
            
        res_exp = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='experience_level'"
        ))
        if not res_exp.fetchone():
            print("Running inline database migration to add experience_level to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN experience_level VARCHAR(50) NULL"))
            conn.commit()
            print("Experience level migration completed.")
            
        res_apify = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='apify_api_token'"
        ))
        if not res_apify.fetchone():
            print("Running inline database migration to add apify_api_token to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN apify_api_token VARCHAR(255) NULL"))
            conn.commit()
            print("Apify API Token migration completed.")

        # Migrate new job API key columns
        for col_name in ['jsearch_api_key', 'adzuna_app_id', 'adzuna_app_key', 'groq_api_key']:
            res_col = conn.execute(text(
                f"SELECT column_name FROM information_schema.columns "
                f"WHERE table_name='users' AND column_name='{col_name}'"
            ))
            if not res_col.fetchone():
                print(f"Running inline database migration to add {col_name} to users table...")
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} VARCHAR(255) NULL"))
                conn.commit()
                print(f"{col_name} migration completed.")

        # Migrate gmail_sync_enabled column
        res_sync = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='gmail_sync_enabled'"
        ))
        if not res_sync.fetchone():
            print("Running inline database migration to add gmail_sync_enabled to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN gmail_sync_enabled BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("gmail_sync_enabled migration completed.")

        # Migrate new job table columns
        res_sen = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='jobs' AND column_name='seniority_level'"
        ))
        if not res_sen.fetchone():
            print("Running inline database migration to add seniority_level to jobs table...")
            conn.execute(text("ALTER TABLE jobs ADD COLUMN seniority_level VARCHAR(50) NULL"))
            conn.commit()
            print("seniority_level migration completed.")

        res_post = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='jobs' AND column_name='posted_at'"
        ))
        if not res_post.fetchone():
            print("Running inline database migration to add posted_at to jobs table...")
            conn.execute(text("ALTER TABLE jobs ADD COLUMN posted_at TIMESTAMP NULL"))
            conn.commit()
            print("posted_at migration completed.")

        res_act = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='jobs' AND column_name='is_active'"
        ))
        if not res_act.fetchone():
            print("Running inline database migration to add is_active to jobs table...")
            conn.execute(text("ALTER TABLE jobs ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
            conn.commit()
            print("is_active migration completed.")
except Exception as migration_err:
    print(f"Inline database migration log (SQLite or already migrated): {migration_err}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("FastAPI application starting...")
    try:
        start_scheduler()
    except Exception as e:
        print(f"Failed to start scheduler on startup: {e}")
    yield
    # Shutdown actions
    print("FastAPI application shutting down...")
    try:
        shutdown_scheduler()
    except Exception as e:
        print(f"Failed to shut down scheduler: {e}")

app = FastAPI(
    title="AI Career Agent API",
    description="Backend API for managing user profiles, parsing resumes, scraping jobs, matching, and tracking applications.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with prefix "/api"
app.include_router(auth.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(gmail.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": os.popen("date").read().strip(),
        "database": "connected"  # Simple sanity placeholder
    }
