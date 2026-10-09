from datetime import date
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Notification, NotificationType, NotificationChannel, PriorityEnum, User
)
from app.api.v1.endpoints.notifications import create_notification_internal


def get_db() -> Session:
    return SessionLocal()


@shared_task
def send_saturday_wheel_reminder():
    """Send Saturday wheel reminder with a direct link to the wheel page."""
    today = date.today()

    # Only run on Saturday (weekday 5)
    if today.weekday() != 5:
        return "Not Saturday, skipping"

    db = get_db()
    try:
        # Check if there are active wheel entries
        from app.models import WheelEntry
        active_entries = db.query(WheelEntry).filter(WheelEntry.is_active == True).count()

        if active_entries == 0:
            return "No active wheel entries"

        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            create_notification_internal(
                db=db,
                user_id=user.id,
                title="🎲 Saturday Random Wheel is Live!",
                message=f"Spin the wheel today for a chance to win! There are {active_entries} prizes available. Open the wheel to spin now.",
                notification_type=NotificationType.WHEEL_REMINDER,
                priority=PriorityEnum.MEDIUM,
                related_entity_type="wheel",
                related_entity_id=None,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                dedup_key=f"wheel_saturday_{today.isoformat()}"
            )

        return f"Sent Saturday wheel reminder to {len(users)} users"
    finally:
        db.close()