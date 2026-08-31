from celery import shared_task
from django.contrib.auth import get_user_model

from rides.services.notification_service import create_notification

User = get_user_model()

@shared_task
def send_reminder_notification(user_id, message):
    print(f"Reminder notification -> User {user_id}: {message}")
    return True


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_notification(
    self,
    user_id,
    title,
    message,
    event_id=None,
):
    user = User.objects.get(id=user_id)

    notification, created = create_notification(
        user=user,
        title=title,
        message=message,
        notification_type="RIDE",
        event_id=event_id,
    )

    print(
        f"Notification "
        f"{'created' if created else 'already exists'} "
        f"for event {event_id}"
    )

    return True


@shared_task(bind=True, max_retries=3)
def test_retry_task(self):
    attempt = self.request.retries + 1

    print(f"Retry test - Attempt {attempt}")

    if attempt < 3:
        raise self.retry(
            exc=Exception(
                f"Simulated failure on attempt {attempt}"
            ),
            countdown=2
        )

    print("Retry test - Success on attempt 3")
    return True