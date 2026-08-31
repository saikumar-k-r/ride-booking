from django.db import transaction
from django.core.cache import cache
from rides.models import Ride, RideStatus, DriverProfile
from django.utils import timezone
def accept_ride(ride_id, user):
    with transaction.atomic():
        # Lock the ride row so two drivers cannot accept it at the same time
        ride = Ride.objects.select_for_update().get(id=ride_id)

        # Ride must be REQUESTED
        if ride.status.code != "REQUESTED":
            raise ValueError("Ride is not available for acceptance.")

        # Get driver profile
        try:
            driver = DriverProfile.objects.get(user=user)
        except DriverProfile.DoesNotExist:
            raise ValueError("Driver profile not found.")

        # Driver must be active
        if not driver.is_active:
            raise ValueError("Driver is not active.")

        # Assign driver and change status
        ride.driver = driver
        ride.status = RideStatus.objects.get(code="ACCEPTED")
        ride.save(update_fields=["driver", "status"])

        return ride
def update_ride_status(ride_id, new_status):
    """
    Update a ride status only when the requested transition
    is allowed.
    """

    allowed_transitions = {
        "REQUESTED": ["ACCEPTED", "CANCELLED"],
        "ACCEPTED": ["DRIVER_ARRIVING", "CANCELLED"],
        "DRIVER_ARRIVING": ["STARTED"],
        "STARTED": ["COMPLETED"],
        "COMPLETED": [],
        "CANCELLED": [],
    }

    with transaction.atomic():
        ride = Ride.objects.select_for_update().get(id=ride_id)

        current_status = ride.status.code

        if new_status not in allowed_transitions.get(
            current_status, []
        ):
            raise ValueError(
                f"Invalid transition: "
                f"{current_status} -> {new_status}"
            )

        try:
            new_status_obj = RideStatus.objects.get(
                code=new_status,
                is_active=True,
            )
        except RideStatus.DoesNotExist:
            raise ValueError("Invalid ride status.")

        ride.status = new_status_obj
        ride.save(update_fields=["status", "updated_at"])

        cache.delete("rides:daily_count")
        cache.delete("rides:total_completed")
        cache.delete("rides:aggregations")

        return ride
def cancel_ride(ride_id, user):
    with transaction.atomic():
        ride = Ride.objects.select_for_update().get(id=ride_id)

        if ride.passenger_id != user.id:
            raise ValueError("You are not allowed to cancel this ride.")

        if ride.status.code not in ["REQUESTED", "ACCEPTED"]:
            raise ValueError(
                f"Ride cannot be cancelled from {ride.status.code} status."
            )

        cancelled_status = RideStatus.objects.get(
            code="CANCELLED",
            is_active=True,
        )

        ride.status = cancelled_status
        ride.save(update_fields=["status", "updated_at"])

        cache.delete("rides:daily_count")
        cache.delete("rides:total_completed")
        cache.delete("rides:aggregations")

        return ride


def start_ride(ride_id, user):
    with transaction.atomic():
        ride = Ride.objects.select_for_update().get(id=ride_id)

        if not ride.driver or ride.driver.user_id != user.id:
            raise ValueError("You are not assigned to this ride.")

        if ride.status.code != "ACCEPTED":
            raise ValueError(
                "Ride must be accepted before starting."
            )

        started_status = RideStatus.objects.get(
            code="STARTED",
            is_active=True,
        )

        ride.status = started_status
        ride.save(update_fields=["status", "updated_at"])

        return ride


def arrive_ride(ride_id, user):
    with transaction.atomic():
        ride = Ride.objects.select_for_update().get(id=ride_id)

        if not ride.driver or ride.driver.user_id != user.id:
            raise ValueError("You are not assigned to this ride.")

        if ride.status.code != "DRIVER_ARRIVING":
            raise ValueError(
                "Ride must be in DRIVER_ARRIVING status."
            )

        arrived_status = RideStatus.objects.get(
            code="ARRIVED",
            is_active=True,
        )

        ride.status = arrived_status
        ride.save(update_fields=["status", "updated_at"])

        return ride


def complete_ride(ride_id, user):
    with transaction.atomic():
        ride = Ride.objects.select_for_update().get(id=ride_id)

        if not ride.driver or ride.driver.user_id != user.id:
            raise ValueError("You are not assigned to this ride.")

        if ride.status.code not in ["STARTED", "ARRIVED"]:
            raise ValueError(
                "Ride must be started before completion."
            )

        completed_status = RideStatus.objects.get(
            code="COMPLETED",
            is_active=True,
        )

        ride.status = completed_status
        ride.completed_at = timezone.now()

        ride.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        cache.delete("rides:daily_count")
        cache.delete("rides:total_completed")
        cache.delete("rides:aggregations")

        return ride