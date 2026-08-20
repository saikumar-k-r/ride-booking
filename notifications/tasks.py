cat > notifications/tasks.py <<'EOF'
from celery import shared_task
from .models import Notification


def create_notification(user, title, message, notification_type="SYSTEM"):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
    )


@shared_task
def send_ride_notification(user_id, title, message):
    print(f"Ride notification → User {user_id}: {title} - {message}")
    return True


@shared_task
def send_driver_assignment_notification(user_id, ride_id):
    print(f"Driver assignment notification → User {user_id}, Ride {ride_id}")
    return True


@shared_task
def send_ride_completion_notification(user_id, ride_id):
    print(f"Ride completion notification → User {user_id}, Ride {ride_id}")
    return True


@shared_task
def send_reminder_notification(user_id, message):
    print(f"Reminder notification → User {user_id}: {message}")
    return True
EOF
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_notification(self, user_id, title, message):
    notification, created = Notification.objects.get_or_create(
        user_id=user_id,
        title=title,
        message=message,
    )

    print(f"Notification {'created' if created else 'already exists'} for user {user_id}")
    return True