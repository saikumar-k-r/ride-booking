from django.db import transaction

from rides.models import Notification


@transaction.atomic
def create_notification(
    user,
    title,
    message,
    notification_type,
    event_id=None,
):
    """
    Create a notification while preventing duplicate events.
    """

    if event_id:
        notification, created = Notification.objects.get_or_create(
            event_id=event_id,
            defaults={
                "user": user,
                "title": title,
                "message": message,
                "notification_type": notification_type,
            },
        )

        return notification, created

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
    )

    return notification, True