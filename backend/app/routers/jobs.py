from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.user_job import UserJob
from app.models.job import Job
from app.schemas.job import JobMatchResponse
from app.utils.auth import get_current_user
from app.services.scraper_service import scraper_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/matches", response_model=List[JobMatchResponse])
def get_job_matches(
    status_filter: Optional[str] = Query(None, alias="status"),
    min_score: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(
        UserJob.id,
        UserJob.job_id,
        Job.title,
        Job.company,
        Job.location,
        Job.description,
        Job.url,
        Job.source,
        UserJob.match_score,
        UserJob.match_rationale,
        UserJob.missing_skills,
        UserJob.matching_skills,
        UserJob.status,
        UserJob.applied_at,
        UserJob.notes,
        UserJob.created_at,
        UserJob.updated_at
    ).join(Job, UserJob.job_id == Job.id).filter(
        UserJob.user_id == current_user.id,
        UserJob.match_score >= min_score
    )
    
    if status_filter:
        query = query.filter(UserJob.status == status_filter)
    else:
        # By default exclude ignored/rejected if not specified? Or return all? 
        # Returning all, but frontend can manage filters. Let's exclude 'ignored' from general feed.
        query = query.filter(UserJob.status != "ignored")
        
    results = query.order_by(UserJob.match_score.desc()).all()
    
    # Format database rows into response schema objects
    return [
        JobMatchResponse(
            id=r[0],
            job_id=r[1],
            title=r[2],
            company=r[3],
            location=r[4],
            description=r[5],
            url=r[6],
            source=r[7],
            match_score=r[8],
            match_rationale=r[9],
            missing_skills=r[10],
            matching_skills=r[11],
            status=r[12],
            applied_at=r[13],
            notes=r[14],
            created_at=r[15],
            updated_at=r[16]
        )
        for r in results
    ]

@router.post("/discover", status_code=status.HTTP_200_OK)
async def trigger_job_discovery(
    query: str = Query("Software Engineer"),
    location: str = Query("Remote"),
    limit: int = Query(10),
    sources: Optional[str] = Query(None),
    use_mock: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sources_list = ["all"]
    if sources:
        sources_list = [s.strip() for s in sources.split(",") if s.strip()]
        
    new_jobs = await scraper_service.discover_and_match_jobs(
        db=db,
        query=query,
        location=location,
        limit=limit,
        sources=sources_list,
        use_mock=use_mock,
        apify_api_token=current_user.apify_api_token,
        jsearch_api_key=current_user.jsearch_api_key,
        adzuna_app_id=current_user.adzuna_app_id,
        adzuna_app_key=current_user.adzuna_app_key
    )
    return {"message": "Job discovery completed successfully", "new_jobs_discovered": new_jobs}
