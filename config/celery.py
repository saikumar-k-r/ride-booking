import os

from celery import Celery
from kombu import Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

# Logical task queues
app.conf.task_queues = (
    Queue("notifications"),
    Queue("reports"),
    Queue("maintenance"),
)

# Route tasks to the appropriate queue
app.conf.task_routes = {
    "notifications.tasks.send_notification": {
        "queue": "notifications",
    },
    "notifications.tasks.send_reminder_notification": {
        "queue": "notifications",
    },
    "notifications.tasks.generate_ride_report": {
        "queue": "reports",
    },
    "notifications.tasks.clean_expired_data": {
        "queue": "maintenance",
    },
    "notifications.tasks.process_background_records": {
        "queue": "maintenance",
    },
    "notifications.tasks.test_retry_task": {
        "queue": "maintenance",
    },
    "notifications.tasks.clean_old_temporary_data": {
    "queue": "maintenance",
    },
}

app.autodiscover_tasks()