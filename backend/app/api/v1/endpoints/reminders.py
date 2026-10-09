from datetime import date, datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, Reminder, ReminderStatus, PriorityEnum,
    ReminderNotificationLog
)
from app.schemas import (
    ReminderCreate, ReminderUpdate, ReminderResponse, ReminderFilter,
    PaginationParams, PaginatedResponse
)


router = APIRouter()


def generate_reminder_schedule(deadline: date, deadline_time: Optional[time], schedule: List[str]) -> List[datetime]:
    """Generate notification datetimes based on reminder schedule."""
    notifications = []
    base_dt = datetime.combine(deadline, deadline_time or time(9, 0))
    
    for item in schedule:
        item_lower = item.lower().strip()
        if "day" in item_lower:
            try:
                days = int(item_lower.split()[0])
                notify_dt = base_dt - timedelta(days=days)
                if notify_dt > datetime.utcnow():
                    notifications.append(notify_dt)
            except (ValueError, IndexError):
                pass
        elif "hour" in item_lower:
            try:
                hours = int(item_lower.split()[0])
                notify_dt = base_dt - timedelta(hours=hours)
                if notify_dt > datetime.utcnow():
                    notifications.append(notify_dt)
            except (ValueError, IndexError):
                pass
        elif "week" in item_lower:
            try:
                weeks = int(item_lower.split()[0])
                notify_dt = base_dt - timedelta(weeks=weeks)
                if notify_dt > datetime.utcnow():
                    notifications.append(notify_dt)
            except (ValueError, IndexError):
                pass
    
    return notifications


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new reminder."""
    reminder = Reminder(
        **reminder_in.model_dump(exclude={"assignee_id"}),
        assignee_id=reminder_in.assignee_id or current_user.id,
        created_by_id=current_user.id,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    # Schedule notifications
    if reminder.reminder_schedule:
        schedule = generate_reminder_schedule(
            reminder.deadline, reminder.deadline_time, reminder.reminder_schedule
        )
        for notify_dt in schedule:
            log = ReminderNotificationLog(
                reminder_id=reminder.id,
                notification_type="in_app",
                scheduled_for=notify_dt,
                status="pending"
            )
            db.add(log)
        db.commit()
    
    return reminder


@router.get("/", response_model=PaginatedResponse)
def list_reminders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ReminderStatus] = None,
    priority: Optional[PriorityEnum] = None,
    assignee_id: Optional[int] = None,
    related_entity_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List reminders with filters and pagination."""
    query = db.query(Reminder)

    # Non-admins only see their own reminders
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Reminder.assignee_id == current_user.id)
    elif assignee_id:
        query = query.filter(Reminder.assignee_id == assignee_id)

    if status:
        query = query.filter(Reminder.status == status)
    if priority:
        query = query.filter(Reminder.priority == priority)
    if related_entity_type:
        query = query.filter(Reminder.related_entity_type == related_entity_type)
    if start_date:
        query = query.filter(Reminder.deadline >= start_date)
    if end_date:
        query = query.filter(Reminder.deadline <= end_date)
    if search:
        query = query.filter(
            or_(
                Reminder.title.ilike(f"%{search}%"),
                Reminder.description.ilike(f"%{search}%")
            )
        )

    total = query.count()
    reminders = query.order_by(Reminder.deadline.asc()).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=reminders,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/upcoming", response_model=List[ReminderResponse])
def get_upcoming_reminders(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get upcoming reminders within specified days."""
    end_date = date.today() + timedelta(days=days)
    query = db.query(Reminder).filter(
        Reminder.deadline >= date.today(),
        Reminder.deadline <= end_date,
        Reminder.status == ReminderStatus.PENDING
    )
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Reminder.assignee_id == current_user.id)
    
    return query.order_by(Reminder.deadline.asc()).all()


@router.get("/overdue", response_model=List[ReminderResponse])
def get_overdue_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overdue reminders."""
    query = db.query(Reminder).filter(
        Reminder.deadline < date.today(),
        Reminder.status == ReminderStatus.PENDING
    )
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Reminder.assignee_id == current_user.id)
    
    return query.order_by(Reminder.deadline.asc()).all()


@router.get("/completed", response_model=List[ReminderResponse])
def get_completed_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get completed reminders."""
    query = db.query(Reminder).filter(Reminder.status == ReminderStatus.COMPLETED)
    
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Reminder.assignee_id == current_user.id)
    
    return query.order_by(Reminder.completed_at.desc()).all()


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get reminder by ID."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    if current_user.role.value not in ["admin", "manager"] and reminder.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return reminder


@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    reminder_update: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a reminder."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    if current_user.role.value not in ["admin", "manager"] and reminder.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = reminder_update.model_dump(exclude_unset=True)
    
    # Handle completion
    if update_data.get("status") == ReminderStatus.COMPLETED and reminder.status != ReminderStatus.COMPLETED:
        update_data["completed_at"] = datetime.utcnow()
        update_data["completed_by_id"] = current_user.id
    
    for field, value in update_data.items():
        setattr(reminder, field, value)
    
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
def complete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark reminder as completed."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    if current_user.role.value not in ["admin", "manager"] and reminder.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    reminder.status = ReminderStatus.COMPLETED
    reminder.completed_at = datetime.utcnow()
    reminder.completed_by_id = current_user.id
    
    # Cancel pending notifications
    pending_logs = db.query(ReminderNotificationLog).filter(
        ReminderNotificationLog.reminder_id == reminder_id,
        ReminderNotificationLog.status == "pending"
    ).all()
    for log in pending_logs:
        log.status = "cancelled"
    
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a reminder."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    if current_user.role.value not in ["admin", "manager"] and reminder.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(reminder)
    db.commit()
    return {"message": "Reminder deleted successfully"}


@router.post("/auto-collect")
def auto_collect_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Auto-collect reminder details from wheel spins, challenges, gifts, and payments.

    Creates Reminder entries automatically so users are reminded without manual typing.
    Idempotent: skips entries that already exist.
    """
    from app.services.reminder_collector import auto_collect_all
    counts = auto_collect_all(db, current_user.id)
    total = sum(counts.values())
    return {"message": f"Collected {total} reminders", "counts": counts}