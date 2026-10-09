from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, Request, RequestStatus, RequestType, PriorityEnum,
    RequestStatusHistory
)
from app.schemas import (
    RequestCreate, RequestUpdate, RequestResponse, RequestFilter,
    RequestStatusHistoryResponse, PaginationParams, PaginatedResponse
)


router = APIRouter()


def generate_request_id(db: Session) -> str:
    """Generate unique request ID like REQ-2024-001."""
    from datetime import datetime
    year = datetime.utcnow().year
    count = db.query(Request).filter(
        Request.request_id.like(f"REQ-{year}-%")
    ).count()
    return f"REQ-{year}-{count + 1:03d}"


@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    request_in: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new request."""
    request = Request(
        **request_in.model_dump(exclude={"assignee_id"}),
        requester_id=current_user.id,
        assignee_id=request_in.assignee_id,
        request_id=generate_request_id(db),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    # Create status history
    history = RequestStatusHistory(
        request_id=request.id,
        new_status=RequestStatus.PENDING,
        changed_by_id=current_user.id,
        notes="Request created"
    )
    db.add(history)
    db.commit()
    
    return request


@router.get("/", response_model=PaginatedResponse)
def list_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[RequestStatus] = None,
    request_type: Optional[RequestType] = None,
    priority: Optional[PriorityEnum] = None,
    assignee_id: Optional[int] = None,
    requester_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List requests with filters and pagination."""
    query = db.query(Request)
    
    # Non-admins only see their own requests (created or assigned)
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(
            or_(Request.requester_id == current_user.id, Request.assignee_id == current_user.id)
        )
    else:
        if assignee_id:
            query = query.filter(Request.assignee_id == assignee_id)
        if requester_id:
            query = query.filter(Request.requester_id == requester_id)
    
    if status:
        query = query.filter(Request.status == status)
    if request_type:
        query = query.filter(Request.request_type == request_type)
    if priority:
        query = query.filter(Request.priority == priority)
    if start_date:
        query = query.filter(Request.requested_date >= start_date)
    if end_date:
        query = query.filter(Request.requested_date <= end_date)
    if search:
        query = query.filter(
            or_(
                Request.title.ilike(f"%{search}%"),
                Request.description.ilike(f"%{search}%"),
                Request.request_id.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    requests = query.order_by(Request.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=requests,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/pending", response_model=List[RequestResponse])
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pending requests requiring admin action."""
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return db.query(Request).filter(
        Request.status.in_([RequestStatus.PENDING, RequestStatus.UNDER_REVIEW])
    ).order_by(Request.priority.desc(), Request.due_date.asc().nullslast()).all()


@router.get("/{request_id}", response_model=RequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get request by ID."""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if current_user.role.value not in ["admin", "manager"]:
        if request.requester_id != current_user.id and request.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return request


@router.patch("/{request_id}", response_model=RequestResponse)
def update_request(
    request_id: int,
    request_update: RequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a request."""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    if current_user.role.value not in ["admin", "manager"]:
        if request.requester_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Requesters can only update certain fields
        allowed_fields = {"title", "description", "supporting_documents"}
        update_data = {k: v for k, v in request_update.model_dump(exclude_unset=True).items() if k in allowed_fields}
    else:
        update_data = request_update.model_dump(exclude_unset=True)
    
    old_status = request.status
    
    for field, value in update_data.items():
        setattr(request, field, value)
    
    # Handle status change
    if "status" in update_data and update_data["status"] != old_status:
        history = RequestStatusHistory(
            request_id=request.id,
            old_status=old_status,
            new_status=update_data["status"],
            changed_by_id=current_user.id,
            notes=request_update.resolution_notes
        )
        db.add(history)
        
        if update_data["status"] in [RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.COMPLETED]:
            request.resolved_by_id = current_user.id
            request.resolved_at = datetime.utcnow()
            if update_data["status"] == RequestStatus.COMPLETED:
                request.completed_date = date.today()
    
    db.commit()
    db.refresh(request)
    return request


@router.post("/{request_id}/approve", response_model=RequestResponse)
def approve_request(
    request_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Approve a request (admin only)."""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status not in [RequestStatus.PENDING, RequestStatus.UNDER_REVIEW]:
        raise HTTPException(status_code=400, detail="Request cannot be approved")
    
    old_status = request.status
    request.status = RequestStatus.APPROVED
    request.resolved_by_id = current_user.id
    request.resolved_at = datetime.utcnow()
    if notes:
        request.resolution_notes = notes
    
    history = RequestStatusHistory(
        request_id=request.id,
        old_status=old_status,
        new_status=RequestStatus.APPROVED,
        changed_by_id=current_user.id,
        notes=notes
    )
    db.add(history)
    db.commit()
    db.refresh(request)
    return request


@router.post("/{request_id}/reject", response_model=RequestResponse)
def reject_request(
    request_id: int,
    notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Reject a request (admin only)."""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status not in [RequestStatus.PENDING, RequestStatus.UNDER_REVIEW]:
        raise HTTPException(status_code=400, detail="Request cannot be rejected")
    
    old_status = request.status
    request.status = RequestStatus.REJECTED
    request.resolved_by_id = current_user.id
    request.resolved_at = datetime.utcnow()
    request.resolution_notes = notes
    
    history = RequestStatusHistory(
        request_id=request.id,
        old_status=old_status,
        new_status=RequestStatus.REJECTED,
        changed_by_id=current_user.id,
        notes=notes
    )
    db.add(history)
    db.commit()
    db.refresh(request)
    return request


@router.post("/{request_id}/complete", response_model=RequestResponse)
def complete_request(
    request_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark request as completed."""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if current_user.role.value not in ["admin", "manager"] and request.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    old_status = request.status
    request.status = RequestStatus.COMPLETED
    request.completed_date = date.today()
    request.resolved_by_id = current_user.id
    request.resolved_at = datetime.utcnow()
    if notes:
        request.resolution_notes = notes
    
    history = RequestStatusHistory(
        request_id=request.id,
        old_status=old_status,
        new_status=RequestStatus.COMPLETED,
        changed_by_id=current_user.id,
        notes=notes
    )
    db.add(history)
    db.commit()
    db.refresh(request)
    return request


@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a request (admin only)."""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    db.delete(request)
    db.commit()
    return {"message": "Request deleted successfully"}