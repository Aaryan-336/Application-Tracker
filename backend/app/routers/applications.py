from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from uuid import UUID
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.user_job import UserJob
from app.models.job import Job
from app.schemas.job import JobMatchResponse
from app.schemas.user_job import UserJobUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("/tracker", response_model=List[JobMatchResponse])
def get_tracked_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Retrieve jobs that are tracked (i.e. status is not 'discovered' and not 'ignored')
    results = db.query(
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
        UserJob.status.in_(["saved", "applied", "assessment", "interview", "offer", "rejected"])
    ).order_by(UserJob.updated_at.desc()).all()
    
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

@router.put("/{user_job_id}/status", response_model=JobMatchResponse)
def update_application_status(
    user_job_id: UUID,
    update_in: UserJobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_job = db.query(UserJob).filter(
        UserJob.id == user_job_id,
        UserJob.user_id == current_user.id
    ).first()
    
    if not user_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracked job not found or unauthorized access."
        )
        
    if update_in.status is not None:
        user_job.status = update_in.status
        # Automate applied_at setting
        if update_in.status == "applied" and not user_job.applied_at:
            user_job.applied_at = datetime.utcnow()
            
    if update_in.applied_at is not None:
        user_job.applied_at = update_in.applied_at
        
    if update_in.notes is not None:
        user_job.notes = update_in.notes
        
    db.commit()
    db.refresh(user_job)
    
    # Get associated job details to build response
    job = db.query(Job).filter(Job.id == user_job.job_id).first()
    
    return JobMatchResponse(
        id=user_job.id,
        job_id=user_job.job_id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        url=job.url,
        source=job.source,
        match_score=user_job.match_score,
        match_rationale=user_job.match_rationale,
        missing_skills=user_job.missing_skills,
        matching_skills=user_job.matching_skills,
        status=user_job.status,
        applied_at=user_job.applied_at,
        notes=user_job.notes,
        created_at=user_job.created_at,
        updated_at=user_job.updated_at
    )

@router.get("/dashboard-stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Total matches
    total_matches = db.query(UserJob).filter(
        UserJob.user_id == current_user.id,
        UserJob.status != "ignored"
    ).count()

    # Discovered count
    discovered_count = db.query(UserJob).filter(
        UserJob.user_id == current_user.id,
        UserJob.status == "discovered"
    ).count()

    # Applications sent (applied + subsequent stages)
    applied_count = db.query(UserJob).filter(
        UserJob.user_id == current_user.id,
        UserJob.status.in_(["applied", "assessment", "interview", "offer", "rejected"])
    ).count()

    # Interviews scheduled
    interview_count = db.query(UserJob).filter(
        UserJob.user_id == current_user.id,
        UserJob.status == "interview"
    ).count()

    # Offers received
    offer_count = db.query(UserJob).filter(
        UserJob.user_id == current_user.id,
        UserJob.status == "offer"
    ).count()

    # Rejected count
    rejected_count = db.query(UserJob).filter(
        UserJob.user_id == current_user.id,
        UserJob.status == "rejected"
    ).count()

    # Average match score
    avg_score_row = db.query(func.avg(UserJob.match_score)).filter(
        UserJob.user_id == current_user.id,
        UserJob.status != "ignored"
    ).first()
    avg_match_score = round(float(avg_score_row[0])) if avg_score_row and avg_score_row[0] is not None else 0

    # Response Rate: (interview + offer + assessment) / applied_count * 100
    positive_outcomes = db.query(UserJob).filter(
        UserJob.user_id == current_user.id,
        UserJob.status.in_(["assessment", "interview", "offer"])
    ).count()
    
    response_rate = 0.0
    if applied_count > 0:
        response_rate = round((positive_outcomes / applied_count) * 100, 1)

    return {
        "totalMatches": total_matches,
        "discoveredCount": discovered_count,
        "appliedCount": applied_count,
        "interviewCount": interview_count,
        "offerCount": offer_count,
        "rejectedCount": rejected_count,
        "avgMatchScore": avg_match_score,
        "responseRate": response_rate
    }
