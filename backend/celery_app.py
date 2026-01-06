from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL")

celery = Celery(
    "crisiswatch",
    broker=REDIS_URL if REDIS_URL else None,
    backend=REDIS_URL if REDIS_URL else None,
)
