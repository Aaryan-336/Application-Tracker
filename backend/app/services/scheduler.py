import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.scraper_service import scraper_service

scheduler = AsyncIOScheduler()

async def scheduled_discovery_job():
    print("Background scheduler: starting daily job discovery...")
    db = SessionLocal()
    try:
        # We run the real scrape (which falls back to mock if there are network issues)
        await scraper_service.discover_and_match_jobs(db, use_mock=False)
    except Exception as e:
        print(f"Error running scheduled job: {e}")
    finally:
        db.close()

async def scheduled_gmail_sync_job():
    print("Background scheduler: starting daily Gmail sync...")
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.services.gmail_service import gmail_service
        users = db.query(User).filter(
            User.gmail_sync_enabled == True,
            User.gmail_address.isnot(None),
            User.gmail_app_password.isnot(None)
        ).all()
        
        print(f"Background scheduler: found {len(users)} users with daily sync active.")
        for u in users:
            try:
                print(f"Background scheduler: syncing Gmail for user: {u.email}")
                # Sync last 3 days of emails to catch any weekend/offline updates
                await gmail_service.sync_user_emails(db, u, days_back=3)
            except Exception as ue:
                print(f"Error syncing Gmail in background for user {u.email}: {ue}")
    except Exception as e:
        print(f"Error running scheduled Gmail sync job: {e}")
    finally:
        db.close()

def start_scheduler():
    # Schedule job to run daily at 2:00 AM
    scheduler.add_job(scheduled_discovery_job, "cron", hour=2, minute=0, id="daily_job_discovery", replace_existing=True)
    
    # Schedule daily Gmail sync to run at 3:00 AM
    scheduler.add_job(scheduled_gmail_sync_job, "cron", hour=3, minute=0, id="daily_gmail_sync", replace_existing=True)
    
    scheduler.start()
    print("APScheduler started successfully.")

def shutdown_scheduler():
    scheduler.shutdown()
    print("APScheduler shut down.")
