from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, Notification, NotificationType, NotificationChannel, PriorityEnum
)
from app.schemas import (
    NotificationCreate, NotificationUpdate, NotificationResponse, NotificationFilter,
    PaginationParams, PaginatedResponse
)


router = APIRouter()


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification_in: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a notification (admin only)."""
    # Check for duplicate using dedup_key
    if notification_in.dedup_key:
        existing = db.query(Notification).filter(
            Notification.dedup_key == notification_in.dedup_key
        ).first()
        if existing:
            return existing
    
    notification = Notification(**notification_in.model_dump())
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/", response_model=PaginatedResponse)
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List notifications for current user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    if start_date:
        query = query.filter(Notification.created_at >= start_date)
    if end_date:
        query = query.filter(Notification.created_at <= end_date)
    
    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=notifications,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/unread-count", response_model=int)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get count of unread notifications."""
    return db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()


@router.get("/recent", response_model=List[NotificationResponse])
def get_recent_notifications(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent notifications for dropdown/panel."""
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(limit).all()


@router.patch("/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update notification (mark as read/unread)."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    update_data = notification_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notification, field, value)
    
    if update_data.get("is_read") is True and not notification.is_read:
        notification.read_at = datetime.utcnow()
    elif update_data.get("is_read") is False:
        notification.read_at = None
    
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True, "read_at": datetime.utcnow()})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted"}


# Helper function for services to create notifications
def create_notification_internal(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType,
    priority: PriorityEnum = PriorityEnum.MEDIUM,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    channels: List[NotificationChannel] = None,
    dedup_key: Optional[str] = None
) -> Notification:
    """Internal function to create notifications from services."""
    if channels is None:
        channels = [NotificationChannel.IN_APP]
    
    # Check dedup
    if dedup_key:
        existing = db.query(Notification).filter(Notification.dedup_key == dedup_key).first()
        if existing:
            return existing
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        channels=[c.value for c in channels],
        dedup_key=dedup_key
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification