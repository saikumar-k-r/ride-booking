from django.db import transaction

from rides.models import DriverProfile, Location


def get_active_driver(user):
    """
    Return the active driver profile for a user.
    """
    try:
        return DriverProfile.objects.get(
            user=user,
            is_active=True,
        )
    except DriverProfile.DoesNotExist:
        raise ValueError("Active driver profile not found.")


@transaction.atomic
def update_driver_location(
    driver,
    latitude,
    longitude,
    availability_status="ONLINE",
):
    """
    Create or update the driver's latest location.
    """

    location = (
        Location.objects
        .filter(driver=driver)
        .order_by("-last_updated")
        .first()
    )

    if location:
        location.latitude = latitude
        location.longitude = longitude
        location.is_available = True
        location.availability_status = availability_status

        location.save(
            update_fields=[
                "latitude",
                "longitude",
                "is_available",
                "availability_status",
                "last_updated",
            ]
        )

    else:
        location = Location.objects.create(
            driver=driver,
            address="",
            latitude=latitude,
            longitude=longitude,
            is_available=True,
            availability_status=availability_status,
        )

    return location