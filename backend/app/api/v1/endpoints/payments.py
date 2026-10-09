from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, Payment, PaymentStatus, PaymentMethod, PriorityEnum,
    PaymentStatusHistory
)
from app.schemas import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentFilter,
    PaymentStatusHistoryResponse, PaymentStatsResponse,
    PaginationParams, PaginatedResponse
)


router = APIRouter()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new payment record."""
    payment = Payment(
        **payment_in.model_dump(exclude={"assignee_id"}),
        assignee_id=payment_in.assignee_id or current_user.id,
        created_by_id=current_user.id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Create initial status history
    history = PaymentStatusHistory(
        payment_id=payment.id,
        new_status=PaymentStatus.PENDING,
        changed_by_id=current_user.id,
        notes="Payment created"
    )
    db.add(history)
    db.commit()
    
    return payment


@router.get("/", response_model=PaginatedResponse)
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[PaymentStatus] = None,
    assignee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List payments with filters and pagination."""
    query = db.query(Payment)
    
    # Non-admins only see their own payments
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Payment.assignee_id == current_user.id)
    elif assignee_id:
        query = query.filter(Payment.assignee_id == assignee_id)
    
    if status:
        query = query.filter(Payment.status == status)
    if start_date:
        query = query.filter(Payment.due_date >= start_date)
    if end_date:
        query = query.filter(Payment.due_date <= end_date)
    if search:
        query = query.filter(
            or_(
                Payment.title.ilike(f"%{search}%"),
                Payment.vendor.ilike(f"%{search}%"),
                Payment.notes.ilike(f"%{search}%")
            )
        )
    if min_amount is not None:
        query = query.filter(Payment.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Payment.amount <= max_amount)
    
    total = query.count()
    payments = query.order_by(Payment.due_date.asc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=payments,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/stats", response_model=PaymentStatsResponse)
def get_payment_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payment statistics."""
    query = db.query(Payment)
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Payment.assignee_id == current_user.id)
    
    stats = query.with_entities(
        func.count(Payment.id).label("total"),
        func.sum(Payment.amount).label("total_amount"),
        func.sum(Payment.amount).filter(Payment.status == PaymentStatus.PENDING).label("pending_amount"),
        func.sum(Payment.amount).filter(Payment.status == PaymentStatus.DUE_SOON).label("due_soon_amount"),
        func.sum(Payment.amount).filter(Payment.status == PaymentStatus.OVERDUE).label("overdue_amount"),
        func.sum(Payment.amount).filter(Payment.status == PaymentStatus.PAID).label("paid_amount"),
    ).first()
    
    counts = db.query(
        Payment.status,
        func.count(Payment.id)
    ).filter(
        Payment.assignee_id == current_user.id if current_user.role.value not in ["admin", "manager"] else True
    ).group_by(Payment.status).all()
    
    count_dict = {status: count for status, count in counts}
    
    return PaymentStatsResponse(
        total_pending=count_dict.get(PaymentStatus.PENDING, 0),
        total_due_soon=count_dict.get(PaymentStatus.DUE_SOON, 0),
        total_overdue=count_dict.get(PaymentStatus.OVERDUE, 0),
        total_paid=count_dict.get(PaymentStatus.PAID, 0),
        total_cancelled=count_dict.get(PaymentStatus.CANCELLED, 0),
        amount_pending=stats.pending_amount or 0,
        amount_paid=stats.paid_amount or 0,
        amount_overdue=stats.overdue_amount or 0,
    )


@router.get("/due-soon", response_model=List[PaymentResponse])
def get_due_soon_payments(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payments due soon."""
    from datetime import timedelta
    end_date = date.today() + timedelta(days=days)
    query = db.query(Payment).filter(
        Payment.due_date >= date.today(),
        Payment.due_date <= end_date,
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON])
    )
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Payment.assignee_id == current_user.id)
    
    return query.order_by(Payment.due_date.asc()).all()


@router.get("/overdue", response_model=List[PaymentResponse])
def get_overdue_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overdue payments."""
    query = db.query(Payment).filter(
        Payment.due_date < date.today(),
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON, PaymentStatus.OVERDUE])
    )
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Payment.assignee_id == current_user.id)
    
    return query.order_by(Payment.due_date.asc()).all()


@router.get("/completed", response_model=List[PaymentResponse])
def get_completed_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get completed payments."""
    query = db.query(Payment).filter(Payment.status == PaymentStatus.PAID)
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Payment.assignee_id == current_user.id)
    
    return query.order_by(Payment.paid_date.desc()).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payment by ID."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if current_user.role.value not in ["admin", "manager"] and payment.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return payment


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if current_user.role.value not in ["admin", "manager"] and payment.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = payment_update.model_dump(exclude_unset=True)
    old_status = payment.status
    
    for field, value in update_data.items():
        setattr(payment, field, value)
    
    # Handle status change
    if "status" in update_data and update_data["status"] != old_status:
        history = PaymentStatusHistory(
            payment_id=payment.id,
            old_status=old_status,
            new_status=update_data["status"],
            changed_by_id=current_user.id,
        )
        db.add(history)
        
        if update_data["status"] == PaymentStatus.PAID:
            payment.paid_date = date.today()
    
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/mark-paid", response_model=PaymentResponse)
def mark_payment_paid(
    payment_id: int,
    payment_method: PaymentMethod,
    payment_reference: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark payment as paid."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if current_user.role.value not in ["admin", "manager"] and payment.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    old_status = payment.status
    payment.status = PaymentStatus.PAID
    payment.payment_method = payment_method
    payment.payment_reference = payment_reference
    payment.paid_date = date.today()
    if notes:
        payment.notes = (payment.notes or "") + f"\n\nPaid: {notes}"
    
    history = PaymentStatusHistory(
        payment_id=payment.id,
        old_status=old_status,
        new_status=PaymentStatus.PAID,
        changed_by_id=current_user.id,
        notes=f"Paid via {payment_method.value}" + (f" (Ref: {payment_reference})" if payment_reference else "")
    )
    db.add(history)
    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a payment (admin only)."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"}