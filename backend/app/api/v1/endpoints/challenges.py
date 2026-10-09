from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, SundayChallenge, ChallengeStatus, ChallengeParticipation
)
from app.schemas import (
    SundayChallengeCreate, SundayChallengeUpdate, SundayChallengeResponse,
    ChallengeParticipationResponse, PaginationParams, PaginatedResponse
)


router = APIRouter()


@router.post("/", response_model=SundayChallengeResponse, status_code=status.HTTP_201_CREATED)
def create_challenge(
    challenge_in: SundayChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new Sunday challenge (admin only)."""
    # Check if challenge already exists for this date
    existing = db.query(SundayChallenge).filter(
        SundayChallenge.challenge_date == challenge_in.challenge_date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Challenge already exists for this date")
    
    challenge = SundayChallenge(
        **challenge_in.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("/", response_model=PaginatedResponse)
def list_challenges(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ChallengeStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List challenges with filters and pagination."""
    query = db.query(SundayChallenge)
    
    if status:
        query = query.filter(SundayChallenge.status == status)
    if start_date:
        query = query.filter(SundayChallenge.challenge_date >= start_date)
    if end_date:
        query = query.filter(SundayChallenge.challenge_date <= end_date)
    
    total = query.count()
    challenges = query.order_by(SundayChallenge.challenge_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=challenges,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/current", response_model=Optional[SundayChallengeResponse])
def get_current_challenge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the current/upcoming Sunday challenge."""
    # Find the most recent Sunday challenge that's not expired
    from datetime import timedelta
    today = date.today()
    
    # Get the most recent challenge (could be past, current, or future)
    challenge = db.query(SundayChallenge).filter(
        SundayChallenge.challenge_date <= today + timedelta(days=7)
    ).order_by(SundayChallenge.challenge_date.desc()).first()
    
    return challenge


@router.get("/{challenge_id}", response_model=SundayChallengeResponse)
def get_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get challenge by ID."""
    challenge = db.query(SundayChallenge).filter(SundayChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@router.patch("/{challenge_id}", response_model=SundayChallengeResponse)
def update_challenge(
    challenge_id: int,
    challenge_update: SundayChallengeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a challenge (admin only)."""
    challenge = db.query(SundayChallenge).filter(SundayChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    update_data = challenge_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(challenge, field, value)
    
    db.commit()
    db.refresh(challenge)
    return challenge


@router.post("/{challenge_id}/participate", response_model=ChallengeParticipationResponse)
def participate_in_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Participate in a challenge."""
    challenge = db.query(SundayChallenge).filter(SundayChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge.status != ChallengeStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Challenge is not active")
    
    # Check if already participating
    existing = db.query(ChallengeParticipation).filter(
        ChallengeParticipation.challenge_id == challenge_id,
        ChallengeParticipation.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already participating in this challenge")
    
    participation = ChallengeParticipation(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status=ChallengeStatus.ACTIVE
    )
    db.add(participation)
    db.commit()
    db.refresh(participation)
    return participation


@router.post("/{challenge_id}/complete", response_model=ChallengeParticipationResponse)
def complete_challenge(
    challenge_id: int,
    submission_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Complete a challenge."""
    participation = db.query(ChallengeParticipation).filter(
        ChallengeParticipation.challenge_id == challenge_id,
        ChallengeParticipation.user_id == current_user.id
    ).first()
    if not participation:
        raise HTTPException(status_code=404, detail="Not participating in this challenge")
    
    participation.status = ChallengeStatus.COMPLETED
    participation.completed_at = datetime.utcnow()
    participation.submission_notes = submission_notes
    
    db.commit()
    db.refresh(participation)
    return participation


@router.get("/{challenge_id}/participations", response_model=List[ChallengeParticipationResponse])
def get_challenge_participations(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all participations for a challenge (admin only)."""
    challenge = db.query(SundayChallenge).filter(SundayChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return db.query(ChallengeParticipation).filter(
        ChallengeParticipation.challenge_id == challenge_id
    ).all()


@router.delete("/{challenge_id}")
def delete_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a challenge (admin only)."""
    challenge = db.query(SundayChallenge).filter(SundayChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    db.delete(challenge)
    db.commit()
    return {"message": "Challenge deleted successfully"}