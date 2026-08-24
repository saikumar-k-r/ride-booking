from django.db.models import Sum, Avg, Max, Min
from django.utils import timezone

from rides.models import Ride


# ============================================================
# RIDE HISTORY
# ============================================================

def get_ride_history():
    return Ride.objects.all().order_by("-created_at")


def get_driver_ride_history(driver):
    return Ride.objects.filter(
        driver=driver
    ).order_by("-created_at")


# ============================================================
# ACTIVE RIDES
# ============================================================

def get_active_rides():
    return Ride.objects.exclude(
        status__code__in=["COMPLETED", "CANCELLED"]
    ).order_by("-created_at")


# ============================================================
# COMPLETED RIDES
# ============================================================

def get_completed_rides():
    return Ride.objects.filter(
        status__code="COMPLETED"
    ).order_by("-created_at")


def get_total_completed_rides():
    return Ride.objects.filter(
        status__code="COMPLETED"
    ).count()


# ============================================================
# CANCELLED RIDES
# ============================================================

def get_cancelled_rides():
    return Ride.objects.filter(
        status__code="CANCELLED"
    ).order_by("-created_at")


# ============================================================
# DAILY RIDE COUNT
# ============================================================

def get_daily_ride_count():
    today = timezone.localdate()

    return Ride.objects.filter(
        created_at__date=today
    ).count()


# ============================================================
# TOTAL FARE
# ============================================================

def get_total_fare_earned():
    result = Ride.objects.filter(
        status__code="COMPLETED"
    ).aggregate(
        total_fare=Sum("fare")
    )

    return result["total_fare"] or 0


# ============================================================
# RIDE AGGREGATION
# ============================================================

def get_ride_aggregations():
    total_rides = Ride.objects.count()

    completed_rides = Ride.objects.filter(
        status__code="COMPLETED"
    ).count()

    cancelled_rides = Ride.objects.filter(
        status__code="CANCELLED"
    ).count()

    fare_data = Ride.objects.filter(
        status__code="COMPLETED"
    ).aggregate(
        total_fare=Sum("fare"),
        average_fare=Avg("fare"),
        maximum_fare=Max("fare"),
        minimum_fare=Min("fare"),
    )

    return {
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "cancelled_rides": cancelled_rides,
        "total_driver_earnings": fare_data["total_fare"] or 0,
        "average_fare": fare_data["average_fare"] or 0,
        "maximum_fare": fare_data["maximum_fare"] or 0,
        "minimum_fare": fare_data["minimum_fare"] or 0,
    }