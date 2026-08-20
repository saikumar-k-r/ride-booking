from django.db import transaction
from rides.models import Ride, RideStatus, DriverProfile
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