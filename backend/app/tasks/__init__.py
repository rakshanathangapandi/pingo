from celery import Celery, crontab
from app.core.config import settings

celery_app = Celery(
    "pingo",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.reminders",
        "app.tasks.notifications",
        "app.tasks.payments",
        "app.tasks.challenges",
        "app.tasks.wheel",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-reminders-every-hour": {
        "task": "app.tasks.reminders.check_and_send_reminders",
        "schedule": 3600.0,  # Every hour
    },
    "auto-collect-reminder-details-daily": {
        "task": "app.tasks.reminders.auto_collect_reminder_details",
        "schedule": 86400.0,  # Daily at midnight
    },
    "check-payments-daily": {
        "task": "app.tasks.payments.check_payment_statuses",
        "schedule": 86400.0,  # Daily at midnight
    },
    "send-challenge-reminder-sunday-7-30pm": {
        "task": "app.tasks.challenges.send_sunday_challenge_reminder",
        "schedule": crontab(hour=19, minute=30, day_of_week=6),  # Sunday 7:30 PM
    },
    "send-wheel-reminder-saturday-7-30pm": {
        "task": "app.tasks.wheel.send_saturday_wheel_reminder",
        "schedule": crontab(hour=19, minute=30, day_of_week=5),  # Saturday 7:30 PM
    },
    "cleanup-old-notifications": {
        "task": "app.tasks.notifications.cleanup_old_notifications",
        "schedule": 604800.0,  # Weekly
    },
}