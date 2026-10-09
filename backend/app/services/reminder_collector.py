"""Auto-collect reminder details from existing activities (wheel, challenges, gifts, payments).

This service scans existing records and auto-creates Reminder entries so admins/users
are reminded without any manual typing. It is idempotent via a dedup key on the
reminder title + entity id.
"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Reminder, ReminderStatus, PriorityEnum,
    WheelSpin, SundayChallenge, ChallengeStatus,
    Gift, GiftStatus, Payment, PaymentStatus,
)
from app.api.v1.endpoints.reminders import generate_reminder_schedule


def get_db() -> Session:
    return SessionLocal()


def _existing(db: Session, dedup_key: str) -> bool:
    return db.query(Reminder).filter(Reminder.title == dedup_key).first() is not None


def collect_from_wheel_spins(db: Session, created_by_id: int) -> int:
    """Auto-create reminders for unclaimed wheel spins."""
    count = 0
    spins = db.query(WheelSpin).filter(WheelSpin.is_claimed == False).all()
    for spin in spins:
        dedup = f"wheel_claim_{spin.id}"
        if _existing(db, dedup):
            continue
        deadline = date.today() + timedelta(days=1)
        reminder = Reminder(
            title=dedup,
            description=f"Claim your wheel prize: {spin.won_label}",
            deadline=deadline,
            deadline_time=None,
            priority=PriorityEnum.MEDIUM,
            status=ReminderStatus.PENDING,
            assignee_id=spin.user_id,
            created_by_id=created_by_id,
            related_entity_type="wheel",
            related_entity_id=spin.id,
            reminder_schedule=["1 day before"],
        )
        db.add(reminder)
        count += 1
    db.commit()
    return count


def collect_from_challenges(db: Session, created_by_id: int) -> int:
    """Auto-create reminders for active challenges that haven't been completed."""
    count = 0
    today = date.today()
    challenges = db.query(SundayChallenge).filter(
        SundayChallenge.status == ChallengeStatus.ACTIVE,
        SundayChallenge.challenge_date >= today,
    ).all()
    for challenge in challenges:
        dedup = f"challenge_{challenge.id}"
        if _existing(db, dedup):
            continue
        reminder = Reminder(
            title=dedup,
            description=f"Complete Sunday challenge: {challenge.title}",
            deadline=challenge.challenge_date,
            deadline_time=None,
            priority=PriorityEnum.HIGH,
            status=ReminderStatus.PENDING,
            assignee_id=None,
            created_by_id=created_by_id,
            related_entity_type="challenge",
            related_entity_id=challenge.id,
            reminder_schedule=["1 day before", "on deadline"],
        )
        db.add(reminder)
        count += 1
    db.commit()
    return count


def collect_from_gifts(db: Session, created_by_id: int) -> int:
    """Auto-create reminders for gifts with upcoming expected delivery."""
    count = 0
    today = date.today()
    soon = today + timedelta(days=7)
    gifts = db.query(Gift).filter(
        Gift.status.in_([GiftStatus.ASSIGNED, GiftStatus.IN_PROGRESS]),
        Gift.expected_delivery_date.isnot(None),
        Gift.expected_delivery_date >= today,
        Gift.expected_delivery_date <= soon,
    ).all()
    for gift in gifts:
        dedup = f"gift_delivery_{gift.id}"
        if _existing(db, dedup):
            continue
        reminder = Reminder(
            title=dedup,
            description=f"Deliver gift: {gift.name} to {gift.recipient.full_name if gift.recipient else 'unassigned'}",
            deadline=gift.expected_delivery_date,
            deadline_time=None,
            priority=PriorityEnum.HIGH,
            status=ReminderStatus.PENDING,
            assignee_id=gift.assignee_id,
            created_by_id=created_by_id,
            related_entity_type="gift",
            related_entity_id=gift.id,
            reminder_schedule=["1 day before"],
        )
        db.add(reminder)
        count += 1
    db.commit()
    return count


def collect_from_payments(db: Session, created_by_id: int) -> int:
    """Auto-create reminders for upcoming/overdue payments."""
    count = 0
    today = date.today()
    soon = today + timedelta(days=7)
    payments = db.query(Payment).filter(
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.DUE_SOON, PaymentStatus.OVERDUE]),
        Payment.due_date <= soon,
    ).all()
    for payment in payments:
        dedup = f"payment_due_{payment.id}"
        if _existing(db, dedup):
            continue
        priority = PriorityEnum.URGENT if payment.status == PaymentStatus.OVERDUE else PriorityEnum.HIGH
        reminder = Reminder(
            title=dedup,
            description=f"Pay {payment.vendor} - ${payment.amount} ({payment.currency})",
            deadline=payment.due_date,
            deadline_time=None,
            priority=priority,
            status=ReminderStatus.PENDING,
            assignee_id=payment.assignee_id,
            created_by_id=created_by_id,
            related_entity_type="payment",
            related_entity_id=payment.id,
            reminder_schedule=["1 day before"],
        )
        db.add(reminder)
        count += 1
    db.commit()
    return count


def auto_collect_all(db: Session, created_by_id: int) -> dict:
    """Run all collectors. Returns counts per source."""
    return {
        "wheel_spins": collect_from_wheel_spins(db, created_by_id),
        "challenges": collect_from_challenges(db, created_by_id),
        "gifts": collect_from_gifts(db, created_by_id),
        "payments": collect_from_payments(db, created_by_id),
    }