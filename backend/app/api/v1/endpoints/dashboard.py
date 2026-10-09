from datetime import date, datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, Reminder, ReminderStatus, Request, RequestStatus, RequestType,
    Payment, PaymentStatus, Asset, AssetStatus, Gift, GiftStatus,
    SundayChallenge, ChallengeStatus, WheelEntry, WheelEntryType,
    PriorityEnum
)
from app.schemas import (
    DashboardStats, UpcomingDeadlineItem, DashboardOverview,
    RequestResponse, PaymentStatsResponse, GiftResponse,
    SundayChallengeResponse
)


router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics."""
    # Base queries - filter by user for non-admins
    def filter_query(query, model):
        if current_user.role.value not in ["admin", "manager"]:
            if hasattr(model, 'assignee_id'):
                return query.filter(model.assignee_id == current_user.id)
            elif hasattr(model, 'user_id'):
                return query.filter(model.user_id == current_user.id)
        return query
    
    # Pending requests
    pending_requests = filter_query(db.query(Request), Request).filter(
        Request.status.in_([RequestStatus.PENDING, RequestStatus.UNDER_REVIEW])
    ).count()
    
    # Pending payments
    pending_payments = filter_query(db.query(Payment), Payment).filter(
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON])
    ).count()
    
    # Overdue payments
    overdue_payments = filter_query(db.query(Payment), Payment).filter(
        Payment.status == PaymentStatus.OVERDUE
    ).count()
    
    # Upcoming deadlines (reminders due in next 7 days)
    upcoming_deadlines = filter_query(db.query(Reminder), Reminder).filter(
        Reminder.deadline >= date.today(),
        Reminder.deadline <= date.today() + timedelta(days=7),
        Reminder.status == ReminderStatus.PENDING
    ).count()
    
    # Total assets
    total_assets = filter_query(db.query(Asset), Asset).count()
    
    # Active challenge
    active_challenge = db.query(SundayChallenge).filter(
        SundayChallenge.status == ChallengeStatus.ACTIVE
    ).order_by(SundayChallenge.challenge_date.desc()).first()
    
    # Gifts
    gifts_query = filter_query(db.query(Gift), Gift)
    gifts_assigned = gifts_query.filter(Gift.status == GiftStatus.ASSIGNED).count()
    gifts_in_progress = gifts_query.filter(Gift.status == GiftStatus.IN_PROGRESS).count()
    gifts_delivered = gifts_query.filter(Gift.status == GiftStatus.DELIVERED).count()
    
    return DashboardStats(
        pending_requests=pending_requests,
        pending_payments=pending_payments,
        overdue_payments=overdue_payments,
        upcoming_deadlines=upcoming_deadlines,
        total_assets=total_assets,
        active_challenge=active_challenge,
        gifts_assigned=gifts_assigned,
        gifts_in_progress=gifts_in_progress,
        gifts_delivered=gifts_delivered
    )


@router.get("/upcoming-deadlines", response_model=List[UpcomingDeadlineItem])
def get_upcoming_deadlines(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get upcoming deadlines from reminders, payments, and gifts."""
    end_date = date.today() + timedelta(days=days)
    items = []
    
    # Reminders
    reminder_query = db.query(Reminder).filter(
        Reminder.deadline >= date.today(),
        Reminder.deadline <= end_date,
        Reminder.status == ReminderStatus.PENDING
    )
    if current_user.role.value not in ["admin", "manager"]:
        reminder_query = reminder_query.filter(Reminder.assignee_id == current_user.id)
    
    for r in reminder_query.order_by(Reminder.deadline.asc()).limit(limit).all():
        items.append(UpcomingDeadlineItem(
            id=r.id,
            title=r.title,
            deadline=r.deadline,
            deadline_time=r.deadline_time,
            priority=r.priority,
            assignee=r.assignee,
            type="reminder"
        ))
    
    # Payments
    payment_query = db.query(Payment).filter(
        Payment.due_date >= date.today(),
        Payment.due_date <= end_date,
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON])
    )
    if current_user.role.value not in ["admin", "manager"]:
        payment_query = payment_query.filter(Payment.assignee_id == current_user.id)
    
    for p in payment_query.order_by(Payment.due_date.asc()).limit(limit).all():
        items.append(UpcomingDeadlineItem(
            id=p.id,
            title=f"{p.title} - {p.vendor} (${p.amount})",
            deadline=p.due_date,
            deadline_time=None,
            priority=PriorityEnum.HIGH if p.status == PaymentStatus.DUE_SOON else PriorityEnum.MEDIUM,
            assignee=p.assignee,
            type="payment"
        ))
    
    # Gifts
    gift_query = db.query(Gift).filter(
        Gift.expected_delivery_date >= date.today(),
        Gift.expected_delivery_date <= end_date,
        Gift.status.in_([GiftStatus.ASSIGNED, GiftStatus.IN_PROGRESS])
    )
    if current_user.role.value not in ["admin", "manager"]:
        gift_query = gift_query.filter(
            or_(Gift.recipient_id == current_user.id, Gift.assignee_id == current_user.id)
        )
    
    for g in gift_query.order_by(Gift.expected_delivery_date.asc()).limit(limit).all():
        items.append(UpcomingDeadlineItem(
            id=g.id,
            title=f"{g.name} - Delivery for {g.recipient.full_name if g.recipient else 'Unknown'}",
            deadline=g.expected_delivery_date,
            deadline_time=None,
            priority=PriorityEnum.HIGH,
            assignee=g.assignee,
            type="gift"
        ))
    
    # Sort by deadline and limit
    items.sort(key=lambda x: (x.deadline, x.deadline_time or time(0, 0)))
    return items[:limit]


@router.get("/pending-requests", response_model=List[RequestResponse])
def get_dashboard_pending_requests(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pending requests for dashboard."""
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return db.query(Request).filter(
        Request.status.in_([RequestStatus.PENDING, RequestStatus.UNDER_REVIEW])
    ).order_by(Request.priority.desc(), Request.due_date.asc().nullslast()).limit(limit).all()


@router.get("/payment-overview", response_model=PaymentStatsResponse)
def get_dashboard_payment_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payment overview for dashboard."""
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


@router.get("/gift-distribution", response_model=List[GiftResponse])
def get_dashboard_gift_distribution(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get gift distribution for dashboard."""
    query = db.query(Gift).filter(
        Gift.status.in_([GiftStatus.ASSIGNED, GiftStatus.IN_PROGRESS, GiftStatus.DELIVERED])
    )
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(
            or_(Gift.recipient_id == current_user.id, Gift.assignee_id == current_user.id)
        )
    
    return query.order_by(Gift.expected_delivery_date.asc().nullslast()).limit(limit).all()


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get complete dashboard overview."""
    stats = get_dashboard_stats(db, current_user)
    upcoming_deadlines = get_upcoming_deadlines(days=7, limit=10, db=db, current_user=current_user)
    pending_requests = get_dashboard_pending_requests(limit=10, db=db, current_user=current_user)
    payment_overview = get_dashboard_payment_overview(db, current_user)
    gift_distribution = get_dashboard_gift_distribution(limit=10, db=db, current_user=current_user)
    
    return DashboardOverview(
        stats=stats,
        upcoming_deadlines=upcoming_deadlines,
        pending_requests=pending_requests,
        payment_overview=payment_overview,
        gift_distribution=gift_distribution
    )