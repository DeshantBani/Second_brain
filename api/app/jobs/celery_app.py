from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery("second_brain", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.beat_schedule = {
    "recheck-all-authorities-every-hour": {
        "task": "app.jobs.monitor.recheck_all_authorities",
        "schedule": crontab(minute=0),  # every hour, on the hour - a demo-friendly cadence
    },
}
celery_app.conf.timezone = "UTC"

# Ensure tasks are registered.
from app.jobs import monitor  # noqa: E402,F401
