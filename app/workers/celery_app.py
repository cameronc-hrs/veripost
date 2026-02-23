"""Celery application configuration.

Connects to Redis as broker and result backend.
Actual tasks will be registered in Phase 2+ plans.
"""

import os

from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

app = Celery(
    "veripost",
    broker=broker_url,
    backend=result_backend,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Auto-discover tasks in app.workers package
app.autodiscover_tasks(["app.workers"])
