from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from rides.models import Ride, Notification
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
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_ride_completion_notification(
    self,
    user_id,
    ride_id,
):
    user = User.objects.get(id=user_id)

    notification, created = create_notification(
        user=user,
        title="Ride Completed",
        message=f"Your ride {ride_id} has been completed.",
        notification_type="RIDE",
        event_id=str(ride_id),
    )

    print(
        f"Ride completion notification "
        f"{'created' if created else 'already exists'} "
        f"for ride {ride_id}"
    )

    return True

@shared_task
def generate_ride_report(user_id=None):
    """
    Generate a ride summary without blocking an API request.
    """
    rides = Ride.objects.all()

    if user_id is not None:
        rides = rides.filter(passenger_id=user_id)

    report = {
        "total_rides": rides.count(),
        "completed_rides": rides.filter(
            status__code="COMPLETED"
        ).count(),
        "requested_rides": rides.filter(
            status__code="REQUESTED"
        ).count(),
        "accepted_rides": rides.filter(
            status__code="ACCEPTED"
        ).count(),
        "cancelled_rides": rides.filter(
            status__code="CANCELLED"
        ).count(),
    }

    print(f"Ride report generated: {report}")

    return report


@shared_task
def clean_expired_data(days=30):
    """
    Remove old read notifications.
    This keeps temporary notification data from growing indefinitely.
    """
    cutoff = timezone.now() - timedelta(days=days)

    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff,
    ).delete()

    print(f"Expired notification records deleted: {deleted_count}")

    return deleted_count
@shared_task
def clean_old_temporary_data(days=7):
    """
    Remove old temporary/read notification data.
    """
    return clean_expired_data(days=days)


@shared_task
def process_background_records(limit=100):
    """
    Process ride records asynchronously.
    The task reads a limited batch so large datasets do not block APIs.
    """
    rides = list(
        Ride.objects.select_related(
            "passenger",
            "driver",
            "vehicle",
            "status",
        )
        .order_by("created_at")[:limit]
    )

    processed_count = 0

    for ride in rides:
        print(
            f"Processing ride {ride.id} "
            f"status={ride.status.code}"
        )
        processed_count += 1

    return {
        "processed": processed_count,
    }


@shared_task(bind=True, max_retries=3)
def test_retry_task(self):
    attempt = self.request.retries + 1

    print(f"Retry test - Attempt {attempt}")

    if attempt < 3:
        raise self.retry(
            exc=Exception(
                f"Simulated failure on attempt {attempt}"
            ),
            countdown=2,
        )

    print("Retry test - Success on attempt 3")

    return True