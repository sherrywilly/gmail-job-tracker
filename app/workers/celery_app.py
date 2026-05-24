from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


celery_app = Celery(
    "gmail_job_tracker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "sync-gmail-inbox": {
        "task": "app.workers.tasks.sync_gmail_inbox",
        "schedule": settings.gmail_poll_interval_minutes * 60,
    },
    "daily-digest": {
        "task": "app.workers.tasks.daily_digest",
        "schedule": crontab(hour=settings.daily_digest_hour_utc, minute=0),
    },
}
