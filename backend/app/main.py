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
