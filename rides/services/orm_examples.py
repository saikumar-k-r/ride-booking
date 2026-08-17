from rides.models import Ride


# filter()
def get_requested_rides():
    return Ride.objects.filter(status__code="REQUESTED")


# exclude()
def get_non_cancelled_rides():
    return Ride.objects.exclude(status__code="CANCELLED")


# get()
def get_ride(ride_id):
    return Ride.objects.get(id=ride_id)


# exists()
def ride_exists(ride_id):
    return Ride.objects.filter(id=ride_id).exists()


# count()
def total_rides():
    return Ride.objects.count()


# values()
def ride_values():
    return Ride.objects.values(
        "id",
        "status",
        "created_at",
    )


# annotate()
from django.db.models import Count

def rides_by_status():
    return Ride.objects.values(
        "status"
    ).annotate(
        total=Count("id")
    )


# aggregate()
from django.db.models import Avg, Max, Min, Sum

def ride_statistics():
    return Ride.objects.aggregate(
        average_fare=Avg("fare"),
        maximum_fare=Max("fare"),
        minimum_fare=Min("fare"),
        total_fare=Sum("fare"),
    )