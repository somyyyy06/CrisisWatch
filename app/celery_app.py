from celery import Celery
from celery.schedules import crontab
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery = Celery("crisis", broker=redis_url, backend=redis_url)

# Celery Beat Schedule: Run scraper every 24 hours
celery.conf.beat_schedule = {
    "scrape-news-every-24h": {
        "task": "app.tasks.scrape_and_store_news",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight UTC
    },
}

# Optional: set timezone
celery.conf.timezone = "UTC"
