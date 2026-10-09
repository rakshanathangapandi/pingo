from datetime import date, datetime
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    SundayChallenge, ChallengeStatus,
    Notification, NotificationType, NotificationChannel, PriorityEnum, User
)
from app.api.v1.endpoints.notifications import create_notification_internal


def get_db() -> Session:
    return SessionLocal()


@shared_task
def send_sunday_challenge_reminder():
    """Send Sunday challenge reminder with a direct link to the challenge page."""
    today = date.today()

    # Only run on Sunday (weekday 6)
    if today.weekday() != 6:
        return "Not Sunday, skipping"

    db = get_db()
    try:
        # Get active challenge for today
        challenge = db.query(SundayChallenge).filter(
            SundayChallenge.challenge_date == today,
            SundayChallenge.status == ChallengeStatus.ACTIVE
        ).first()

        if not challenge:
            return "No active challenge for today"

        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            create_notification_internal(
                db=db,
                user_id=user.id,
                title=f"🎯 Sunday Challenge: {challenge.title}",
                message=f"{challenge.description or ''}\n\nInstructions: {challenge.instructions or 'No specific instructions'}\n\nReward: {challenge.reward or 'To be announced'}\n\nOpen the challenges page to participate.",
                notification_type=NotificationType.CHALLENGE_REMINDER,
                priority=PriorityEnum.MEDIUM,
                related_entity_type="challenge",
                related_entity_id=challenge.id,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                dedup_key=f"challenge_sunday_{challenge.id}_{today.isoformat()}"
            )

        return f"Sent Sunday challenge reminder to {len(users)} users"
    finally:
        db.close()


@shared_task
def expire_old_challenges():
    """Mark old challenges as expired."""
    db = get_db()
    try:
        today = date.today()

        expired = db.query(SundayChallenge).filter(
            SundayChallenge.challenge_date < today,
            SundayChallenge.status == ChallengeStatus.ACTIVE
        ).all()

        for challenge in expired:
            challenge.status = ChallengeStatus.EXPIRED

        db.commit()
        return f"Expired {len(expired)} challenges"
    finally:
        db.close()