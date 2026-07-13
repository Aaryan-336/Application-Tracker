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

def start_scheduler():
    # Schedule job to run daily at 2:00 AM
    scheduler.add_job(scheduled_discovery_job, "cron", hour=2, minute=0, id="daily_job_discovery", replace_existing=True)
    
    # We can also add an interval job for development/demo testing if needed (e.g. every 6 hours)
    # scheduler.add_job(scheduled_discovery_job, "interval", hours=6, id="interval_job_discovery", replace_existing=True)
    
    scheduler.start()
    print("APScheduler started successfully.")

def shutdown_scheduler():
    scheduler.shutdown()
    print("APScheduler shut down.")
