from datetime import date, datetime, timedelta
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.models import (
    Payment, PaymentStatus,
    Notification, NotificationType, NotificationChannel, PriorityEnum, User
)
from app.api.v1.endpoints.notifications import create_notification_internal


def get_db() -> Session:
    return SessionLocal()


@shared_task
def check_payment_statuses():
    """Check and update payment statuses (due soon, overdue)."""
    db = get_db()
    try:
        today = date.today()
        due_soon_date = today + timedelta(days=7)
        
        # Update pending -> due_soon
        due_soon_payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING,
            Payment.due_date <= due_soon_date,
            Payment.due_date >= today,
            Payment.reminder_sent_due_soon == False
        ).all()
        
        for payment in due_soon_payments:
            payment.status = PaymentStatus.DUE_SOON
            payment.reminder_sent_due_soon = True
            
            # Notify assignee
            if payment.assignee_id:
                create_notification_internal(
                    db=db,
                    user_id=payment.assignee_id,
                    title=f"Payment Due Soon: {payment.title}",
                    message=f"Payment of ${payment.amount} to {payment.vendor} is due on {payment.due_date}",
                    notification_type=NotificationType.PAYMENT_DUE,
                    priority=PriorityEnum.HIGH,
                    related_entity_type="payment",
                    related_entity_id=payment.id,
                    channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                    dedup_key=f"payment_due_soon_{payment.id}"
                )
        
        # Update due_soon/pending -> overdue
        overdue_payments = db.query(Payment).filter(
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON]),
            Payment.due_date < today,
            Payment.reminder_sent_overdue == False
        ).all()
        
        for payment in overdue_payments:
            payment.status = PaymentStatus.OVERDUE
            payment.reminder_sent_overdue = True
            
            # Notify assignee
            if payment.assignee_id:
                days_overdue = (today - payment.due_date).days
                create_notification_internal(
                    db=db,
                    user_id=payment.assignee_id,
                    title=f"OVERDUE Payment: {payment.title}",
                    message=f"Payment of ${payment.amount} to {payment.vendor} is {days_overdue} day(s) overdue (due {payment.due_date})",
                    notification_type=NotificationType.PAYMENT_OVERDUE,
                    priority=PriorityEnum.URGENT,
                    related_entity_type="payment",
                    related_entity_id=payment.id,
                    channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                    dedup_key=f"payment_overdue_{payment.id}_{today.isoformat()}"
                )
        
        db.commit()
        return f"Updated {len(due_soon_payments)} to due_soon, {len(overdue_payments)} to overdue"
    finally:
        db.close()


@shared_task
def send_payment_reminders():
    """Send payment reminders for upcoming due dates."""
    db = get_db()
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        three_days = today + timedelta(days=3)
        
        # Due tomorrow
        due_tomorrow = db.query(Payment).filter(
            Payment.due_date == tomorrow,
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON])
        ).all()
        
        for payment in due_tomorrow:
            if payment.assignee_id:
                create_notification_internal(
                    db=db,
                    user_id=payment.assignee_id,
                    title=f"Payment Due Tomorrow: {payment.title}",
                    message=f"Payment of ${payment.amount} to {payment.vendor} is due tomorrow",
                    notification_type=NotificationType.PAYMENT_DUE,
                    priority=PriorityEnum.HIGH,
                    related_entity_type="payment",
                    related_entity_id=payment.id,
                    channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                    dedup_key=f"payment_due_tomorrow_{payment.id}"
                )
        
        # Due in 3 days
        due_3_days = db.query(Payment).filter(
            Payment.due_date == three_days,
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON])
        ).all()
        
        for payment in due_3_days:
            if payment.assignee_id:
                create_notification_internal(
                    db=db,
                    user_id=payment.assignee_id,
                    title=f"Payment Due in 3 Days: {payment.title}",
                    message=f"Payment of ${payment.amount} to {payment.vendor} is due on {three_days}",
                    notification_type=NotificationType.PAYMENT_DUE,
                    priority=PriorityEnum.MEDIUM,
                    related_entity_type="payment",
                    related_entity_id=payment.id,
                    channels=[NotificationChannel.IN_APP],
                    dedup_key=f"payment_due_3days_{payment.id}"
                )
        
        return f"Sent payment reminders: {len(due_tomorrow)} due tomorrow, {len(due_3_days)} due in 3 days"
    finally:
        db.close()