from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, Gift, GiftStatus,
    GiftStatusHistory
)
from app.schemas import (
    GiftCreate, GiftUpdate, GiftResponse, GiftFilter,
    GiftStatusHistoryResponse, GiftStatsResponse,
    PaginationParams, PaginatedResponse
)


router = APIRouter()


def generate_gift_id(db: Session) -> str:
    """Generate unique gift ID like GFT-2024-001."""
    from datetime import datetime
    year = datetime.utcnow().year
    count = db.query(Gift).filter(
        Gift.gift_id.like(f"GFT-{year}-%")
    ).count()
    return f"GFT-{year}-{count + 1:03d}"


@router.post("/", response_model=GiftResponse, status_code=status.HTTP_201_CREATED)
def create_gift(
    gift_in: GiftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new gift record (admin only)."""
    # Check if gift_id already exists
    existing = db.query(Gift).filter(Gift.gift_id == gift_in.gift_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Gift ID already exists")
    
    gift = Gift(
        **gift_in.model_dump(exclude={"recipient_id", "assignee_id"}),
        recipient_id=gift_in.recipient_id,
        assignee_id=gift_in.assignee_id or current_user.id,
        assigned_by_id=current_user.id,
    )
    db.add(gift)
    db.commit()
    db.refresh(gift)
    
    # Create initial status history
    history = GiftStatusHistory(
        gift_id=gift.id,
        new_status=GiftStatus.ASSIGNED,
        changed_by_id=current_user.id,
        notes="Gift assigned"
    )
    db.add(history)
    db.commit()
    
    return gift


@router.get("/", response_model=PaginatedResponse)
def list_gifts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[GiftStatus] = None,
    recipient_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List gifts with filters and pagination."""
    query = db.query(Gift)
    
    # Non-admins only see gifts they're involved with
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(
            or_(Gift.recipient_id == current_user.id, Gift.assignee_id == current_user.id)
        )
    else:
        if recipient_id:
            query = query.filter(Gift.recipient_id == recipient_id)
        if assignee_id:
            query = query.filter(Gift.assignee_id == assignee_id)
    
    if status:
        query = query.filter(Gift.status == status)
    if start_date:
        query = query.filter(Gift.assigned_date >= start_date)
    if end_date:
        query = query.filter(Gift.assigned_date <= end_date)
    if search:
        query = query.filter(
            or_(
                Gift.name.ilike(f"%{search}%"),
                Gift.gift_id.ilike(f"%{search}%"),
                Gift.description.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    gifts = query.order_by(Gift.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=gifts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/stats", response_model=GiftStatsResponse)
def get_gift_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get gift statistics."""
    query = db.query(Gift)
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(
            or_(Gift.recipient_id == current_user.id, Gift.assignee_id == current_user.id)
        )
    
    counts = query.with_entities(
        Gift.status,
        func.count(Gift.id)
    ).group_by(Gift.status).all()
    
    count_dict = {status: count for status, count in counts}
    
    # Count overdue (expected delivery date passed but not delivered)
    overdue = query.filter(
        Gift.expected_delivery_date < date.today(),
        Gift.status.in_([GiftStatus.ASSIGNED, GiftStatus.IN_PROGRESS])
    ).count()
    
    return GiftStatsResponse(
        total=sum(count_dict.values()),
        assigned=count_dict.get(GiftStatus.ASSIGNED, 0),
        in_progress=count_dict.get(GiftStatus.IN_PROGRESS, 0),
        delivered=count_dict.get(GiftStatus.DELIVERED, 0),
        cancelled=count_dict.get(GiftStatus.CANCELLED, 0),
        overdue=overdue
    )


@router.get("/overdue", response_model=List[GiftResponse])
def get_overdue_gifts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overdue gifts."""
    query = db.query(Gift).filter(
        Gift.expected_delivery_date < date.today(),
        Gift.status.in_([GiftStatus.ASSIGNED, GiftStatus.IN_PROGRESS])
    )
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(
            or_(Gift.recipient_id == current_user.id, Gift.assignee_id == current_user.id)
        )
    
    return query.order_by(Gift.expected_delivery_date.asc()).all()


@router.get("/{gift_id}", response_model=GiftResponse)
def get_gift(
    gift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get gift by ID."""
    gift = db.query(Gift).filter(Gift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    
    if current_user.role.value not in ["admin", "manager"]:
        if gift.recipient_id != current_user.id and gift.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return gift


@router.patch("/{gift_id}", response_model=GiftResponse)
def update_gift(
    gift_id: int,
    gift_update: GiftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a gift."""
    gift = db.query(Gift).filter(Gift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    
    if current_user.role.value not in ["admin", "manager"] and gift.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = gift_update.model_dump(exclude_unset=True)
    old_status = gift.status
    
    for field, value in update_data.items():
        setattr(gift, field, value)
    
    # Handle status change
    if "status" in update_data and update_data["status"] != old_status:
        history = GiftStatusHistory(
            gift_id=gift.id,
            old_status=old_status,
            new_status=update_data["status"],
            changed_by_id=current_user.id,
        )
        db.add(history)
        
        if update_data["status"] == GiftStatus.DELIVERED:
            gift.actual_delivery_date = date.today()
    
    db.commit()
    db.refresh(gift)
    return gift


@router.post("/{gift_id}/start-delivery", response_model=GiftResponse)
def start_delivery(
    gift_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark gift as in progress (start delivery)."""
    gift = db.query(Gift).filter(Gift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    
    if current_user.role.value not in ["admin", "manager"] and gift.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if gift.status != GiftStatus.ASSIGNED:
        raise HTTPException(status_code=400, detail="Gift must be in 'Assigned' status")
    
    old_status = gift.status
    gift.status = GiftStatus.IN_PROGRESS
    if notes:
        gift.delivery_notes = (gift.delivery_notes or "") + f"\n\nDelivery started: {notes}"
    
    history = GiftStatusHistory(
        gift_id=gift.id,
        old_status=old_status,
        new_status=GiftStatus.IN_PROGRESS,
        changed_by_id=current_user.id,
        notes=notes
    )
    db.add(history)
    db.commit()
    db.refresh(gift)
    return gift


@router.post("/{gift_id}/deliver", response_model=GiftResponse)
def deliver_gift(
    gift_id: int,
    proof_document: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark gift as delivered."""
    gift = db.query(Gift).filter(Gift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    
    if current_user.role.value not in ["admin", "manager"] and gift.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if gift.status not in [GiftStatus.ASSIGNED, GiftStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="Gift cannot be delivered from current status")
    
    old_status = gift.status
    gift.status = GiftStatus.DELIVERED
    gift.actual_delivery_date = date.today()
    if proof_document:
        gift.proof_document = proof_document
    if notes:
        gift.delivery_notes = (gift.delivery_notes or "") + f"\n\nDelivered: {notes}"
    
    history = GiftStatusHistory(
        gift_id=gift.id,
        old_status=old_status,
        new_status=GiftStatus.DELIVERED,
        changed_by_id=current_user.id,
        notes=f"Proof: {proof_document}" if proof_document else notes
    )
    db.add(history)
    db.commit()
    db.refresh(gift)
    return gift


@router.delete("/{gift_id}")
def delete_gift(
    gift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a gift (admin only)."""
    gift = db.query(Gift).filter(Gift.id == gift_id).first()
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    
    db.delete(gift)
    db.commit()
    return {"message": "Gift deleted successfully"}