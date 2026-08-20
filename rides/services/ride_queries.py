from django.db.models import Count, Sum
from rides.models import Ride


# 1. User's active rides
def get_active_rides(user):
    return Ride.objects.filter(
        user=user,
        status__code__in=[
            "REQUESTED",
            "ACCEPTED",
            "STARTED",
            "DRIVER_ARRIVING",
        ]
    ).order_by("-created_at")


# 2. Completed rides
def get_completed_rides():
    return Ride.objects.filter(
        status__code="COMPLETED"
    ).order_by("-created_at")


# 3. Cancelled rides
def get_cancelled_rides():
    return Ride.objects.filter(
        status__code="CANCELLED"
    ).order_by("-created_at")


# 4. Driver's ride history
def get_driver_ride_history(driver):
    return Ride.objects.filter(
        driver=driver
    ).order_by("-created_at")


# 5. Daily ride count
def get_daily_ride_count():
    return Ride.objects.values(
        "created_at__date"
    ).annotate(
        total_rides=Count("id")
    ).order_by("-created_at__date")


# 6. Total completed rides
def get_total_completed_rides():
    return Ride.objects.filter(
        status__code="COMPLETED"
    ).count()


# 7. Total fare earned
def get_total_fare_earned(driver=None):
    queryset = Ride.objects.filter(
        status__code="COMPLETED"
    )

    if driver:
        queryset = queryset.filter(driver=driver)

    return queryset.aggregate(
        total_fare=Sum("fare")
    )