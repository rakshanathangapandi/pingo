from datetime import datetime, date, time, timedelta
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import SessionLocal
from app.models import (
    Reminder, ReminderStatus, ReminderNotificationLog,
    Notification, NotificationType, NotificationChannel, PriorityEnum, User
)
from app.api.v1.endpoints.notifications import create_notification_internal


def get_db() -> Session:
    return SessionLocal()


@shared_task
def auto_collect_reminder_details():
    """Periodically scan wheel/challenge/gift/payment data and auto-create reminders.

    This ensures users are reminded about upcoming activities without any manual typing.
    """
    db = get_db()
    try:
        from app.services.reminder_collector import auto_collect_all

        # Use the first active admin as the creator for auto-collected reminders
        admin = db.query(User).filter(User.is_active == True, User.is_superuser == True).first()
        if not admin:
            admin = db.query(User).filter(User.is_active == True).first()
        if not admin:
            return "No active users to attribute auto-collected reminders to"

        counts = auto_collect_all(db, admin.id)
        total = sum(counts.values())
        return f"Auto-collected {total} reminders: {counts}"
    finally:
        db.close()


@shared_task
def check_and_send_reminders():
    """Check for due reminders and send notifications."""
    db = get_db()
    try:
        now = datetime.utcnow()
        
        # Find pending notification logs that are due
        due_logs = db.query(ReminderNotificationLog).filter(
            ReminderNotificationLog.status == "pending",
            ReminderNotificationLog.scheduled_for <= now
        ).all()
        
        for log in due_logs:
            reminder = db.query(Reminder).filter(Reminder.id == log.reminder_id).first()
            if not reminder or reminder.status != ReminderStatus.PENDING:
                log.status = "cancelled"
                db.commit()
                continue
            
            # Create in-app notification for assignee
            if reminder.assignee_id:
                create_notification_internal(
                    db=db,
                    user_id=reminder.assignee_id,
                    title=f"Reminder: {reminder.title}",
                    message=reminder.description or f"Deadline: {reminder.deadline}",
                    notification_type=NotificationType.DEADLINE_UPCOMING,
                    priority=reminder.priority,
                    related_entity_type="reminder",
                    related_entity_id=reminder.id,
                    channels=[NotificationChannel.IN_APP],
                    dedup_key=f"reminder_{reminder.id}_{log.scheduled_for.isoformat()}"
                )
            
            log.status = "sent"
            log.sent_at = datetime.utcnow()
            db.commit()
        
        return f"Processed {len(due_logs)} reminder notifications"
    finally:
        db.close()


@shared_task
def send_deadline_reminders():
    """Send reminders for upcoming deadlines (1 day, 3 days before)."""
    db = get_db()
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        three_days = today + timedelta(days=3)
        
        # Find reminders due tomorrow
        due_tomorrow = db.query(Reminder).filter(
            Reminder.deadline == tomorrow,
            Reminder.status == ReminderStatus.PENDING
        ).all()
        
        for reminder in due_tomorrow:
            if reminder.assignee_id:
                create_notification_internal(
                    db=db,
                    user_id=reminder.assignee_id,
                    title=f"Due Tomorrow: {reminder.title}",
                    message=f"This reminder is due tomorrow ({tomorrow}). {reminder.description or ''}",
                    notification_type=NotificationType.DEADLINE_UPCOMING,
                    priority=PriorityEnum.HIGH,
                    related_entity_type="reminder",
                    related_entity_id=reminder.id,
                    channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                    dedup_key=f"reminder_due_tomorrow_{reminder.id}"
                )
        
        # Find reminders due in 3 days
        due_3_days = db.query(Reminder).filter(
            Reminder.deadline == three_days,
            Reminder.status == ReminderStatus.PENDING
        ).all()
        
        for reminder in due_3_days:
            if reminder.assignee_id:
                create_notification_internal(
                    db=db,
                    user_id=reminder.assignee_id,
                    title=f"Due in 3 Days: {reminder.title}",
                    message=f"This reminder is due on {three_days}. {reminder.description or ''}",
                    notification_type=NotificationType.DEADLINE_UPCOMING,
                    priority=PriorityEnum.MEDIUM,
                    related_entity_type="reminder",
                    related_entity_id=reminder.id,
                    channels=[NotificationChannel.IN_APP],
                    dedup_key=f"reminder_due_3days_{reminder.id}"
                )
        
        return f"Sent reminders for {len(due_tomorrow)} due tomorrow, {len(due_3_days)} due in 3 days"
    finally:
        db.close()


@shared_task
def send_overdue_reminders():
    """Send notifications for overdue reminders."""
    db = get_db()
    try:
        yesterday = date.today() - timedelta(days=1)
        
        overdue = db.query(Reminder).filter(
            Reminder.deadline < date.today(),
            Reminder.status == ReminderStatus.PENDING
        ).all()
        
        for reminder in overdue:
            if reminder.assignee_id:
                days_overdue = (date.today() - reminder.deadline).days
                create_notification_internal(
                    db=db,
                    user_id=reminder.assignee_id,
                    title=f"OVERDUE: {reminder.title}",
                    message=f"This reminder was due {days_overdue} day(s) ago ({reminder.deadline}). Please complete it.",
                    notification_type=NotificationType.DEADLINE_OVERDUE,
                    priority=PriorityEnum.URGENT,
                    related_entity_type="reminder",
                    related_entity_id=reminder.id,
                    channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                    dedup_key=f"reminder_overdue_{reminder.id}_{date.today().isoformat()}"
                )
        
        return f"Sent overdue notifications for {len(overdue)} reminders"
    finally:
        db.close()