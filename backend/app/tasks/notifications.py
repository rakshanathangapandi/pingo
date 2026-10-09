from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Notification


def get_db() -> Session:
    return SessionLocal()


@shared_task
def cleanup_old_notifications():
    """Clean up old read notifications (older than 30 days)."""
    db = get_db()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        deleted = db.query(Notification).filter(
            Notification.is_read == True,
            Notification.read_at < cutoff
        ).delete(synchronize_session=False)
        
        db.commit()
        return f"Deleted {deleted} old notifications"
    finally:
        db.close()


@shared_task
def send_email_notification(user_id: int, notification_id: int):
    """Send email notification (placeholder - integrate with actual email service)."""
    db = get_db()
    try:
        from app.models import Notification, User
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not notification or not user:
            return "Notification or user not found"
        
        # TODO: Integrate with actual email service (SendGrid, SMTP, etc.)
        # For now, just log
        print(f"Sending email to {user.email}: {notification.title}")
        
        return f"Email sent to {user.email}"
    finally:
        db.close()


@shared_task
def send_push_notification(user_id: int, notification_id: int):
    """Send web push notification (placeholder)."""
    db = get_db()
    try:
        from app.models import Notification, User, PushSubscription
        from pywebpush import webpush
        from app.core.config import settings
        import json
        
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not notification or not user:
            return "Notification or user not found"
        
        subscriptions = db.query(PushSubscription).filter(
            PushSubscription.user_id == user_id
        ).all()
        
        if not subscriptions:
            return "No push subscriptions"
        
        vapid_claims = {"sub": settings.VAPID_CLAIMS_SUB}
        
        for sub in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh,
                            "auth": sub.auth
                        }
                    },
                    data=json.dumps({
                        "title": notification.title,
                        "body": notification.message,
                        "icon": "/icon-192.png",
                        "data": {
                            "url": f"/notifications/{notification.id}",
                            "type": notification.notification_type.value
                        }
                    }),
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims
                )
            except Exception as e:
                print(f"Push notification failed: {e}")
        
        return f"Push sent to {len(subscriptions)} subscriptions"
    finally:
        db.close()