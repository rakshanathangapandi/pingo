from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import random

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, WheelEntry, WheelEntryType, WheelSpin
)
from app.schemas import (
    WheelEntryCreate, WheelEntryUpdate, WheelEntryResponse,
    WheelSpinCreate, WheelSpinResponse, PaginationParams, PaginatedResponse
)


router = APIRouter()


def pick_wheel_entry(db: Session) -> WheelEntry:
    """Pick a wheel entry based on probabilities."""
    entries = db.query(WheelEntry).filter(WheelEntry.is_active == True).all()
    if not entries:
        raise HTTPException(status_code=400, detail="No active wheel entries")
    
    # Calculate weights
    weights = [entry.probability for entry in entries]
    total_weight = sum(weights)
    if total_weight == 0:
        weights = [1.0] * len(entries)
    
    # Pick random entry based on weights
    rand = random.uniform(0, total_weight)
    cumulative = 0
    for entry, weight in zip(entries, weights):
        cumulative += weight
        if rand <= cumulative:
            return entry
    
    return entries[-1]


@router.post("/entries", response_model=WheelEntryResponse, status_code=status.HTTP_201_CREATED)
def create_wheel_entry(
    entry_in: WheelEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new wheel entry (admin only)."""
    entry = WheelEntry(**entry_in.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/entries", response_model=List[WheelEntryResponse])
def list_wheel_entries(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List wheel entries."""
    query = db.query(WheelEntry)
    if active_only:
        query = query.filter(WheelEntry.is_active == True)
    return query.order_by(WheelEntry.order.asc(), WheelEntry.id.asc()).all()


@router.get("/entries/{entry_id}", response_model=WheelEntryResponse)
def get_wheel_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get wheel entry by ID."""
    entry = db.query(WheelEntry).filter(WheelEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Wheel entry not found")
    return entry


@router.patch("/entries/{entry_id}", response_model=WheelEntryResponse)
def update_wheel_entry(
    entry_id: int,
    entry_update: WheelEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a wheel entry (admin only)."""
    entry = db.query(WheelEntry).filter(WheelEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Wheel entry not found")
    
    update_data = entry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/entries/{entry_id}")
def delete_wheel_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a wheel entry (admin only)."""
    entry = db.query(WheelEntry).filter(WheelEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Wheel entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Wheel entry deleted successfully"}


@router.post("/spin", response_model=WheelSpinResponse)
def spin_wheel(
    spin_in: WheelSpinCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Spin the wheel."""
    # Check if user already spun today
    today = date.today()
    existing = db.query(WheelSpin).filter(
        WheelSpin.user_id == current_user.id,
        WheelSpin.spin_date == today
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already spun today. Try again tomorrow!")
    
    # Pick random entry
    entry = pick_wheel_entry(db)
    
    # Create spin record
    spin = WheelSpin(
        user_id=current_user.id,
        entry_id=entry.id,
        won_label=entry.label,
        won_value=entry.value,
        won_entry_type=entry.entry_type,
        spin_date=today,
    )
    db.add(spin)
    db.commit()
    db.refresh(spin)
    return spin


@router.get("/spins", response_model=PaginatedResponse)
def list_wheel_spins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List wheel spins with filters and pagination."""
    query = db.query(WheelSpin)
    
    # Non-admins only see their own spins
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(WheelSpin.user_id == current_user.id)
    elif user_id:
        query = query.filter(WheelSpin.user_id == user_id)
    
    if start_date:
        query = query.filter(WheelSpin.spin_date >= start_date)
    if end_date:
        query = query.filter(WheelSpin.spin_date <= end_date)
    
    total = query.count()
    spins = query.order_by(WheelSpin.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=spins,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/spins/my", response_model=List[WheelSpinResponse])
def get_my_spins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's spins."""
    return db.query(WheelSpin).filter(
        WheelSpin.user_id == current_user.id
    ).order_by(WheelSpin.created_at.desc()).all()


@router.post("/spins/{spin_id}/claim", response_model=WheelSpinResponse)
def claim_spin(
    spin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Claim a spin reward."""
    spin = db.query(WheelSpin).filter(WheelSpin.id == spin_id).first()
    if not spin:
        raise HTTPException(status_code=404, detail="Spin not found")
    
    if spin.user_id != current_user.id and current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if spin.is_claimed:
        raise HTTPException(status_code=400, detail="Already claimed")
    
    spin.is_claimed = True
    spin.claimed_at = datetime.utcnow()
    db.commit()
    db.refresh(spin)
    return spin