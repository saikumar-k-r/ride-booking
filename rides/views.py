from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .services.fare_service import calculate_fare
from .services.ride_service import accept_ride,update_ride_status
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view,permission_classes
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from django.db import connection
from django.db.models import Q, F, Count, Sum, Avg, Min, Max
from rides.models import Ride
from django.core.cache import cache
from .utils.helpers import success_response, error_response

from .serializers import DriverLocationSerializer
from rides.services.location_service import find_nearby_drivers
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.pagination import PageNumberPagination
from .models import Notification
from .serializers import NotificationSerializer


from .permissions import IsAdminUserRole, IsDriverUser
from .models import DriverProfile, Vehicle,Ride,RideStatus,Location
from .serializers import DriverSerializer, VehicleSerializer, RideSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from .services.ride_queries import (
    get_ride_history,
    get_active_rides,
    get_completed_rides,
    get_cancelled_rides,
    get_driver_ride_history,
    get_daily_ride_count,
    get_total_completed_rides,
    get_total_fare_earned,
)


# =========================
# DRIVER APIs
# =========================

class DriverListCreateAPIView(generics.ListCreateAPIView):
    queryset = DriverProfile.objects.all()
    serializer_class = DriverSerializer

    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "user__username",
        "license_number",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "license_number",
    ]

    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUserRole()]
        return [IsAuthenticated()]

class DriverDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = DriverProfile.objects.all()
    serializer_class = DriverSerializer

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAdminUserRole()]
        return [IsAuthenticated()]



# =========================
# VEHICLE APIs
# =========================

class VehicleListCreateAPIView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "registration_number",
        "model_name",
        "vehicle_type__name",
        "driver__user__username",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "registration_number",
        "model_name",
    ]

    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Vehicle.objects.all()

        vehicle_type = self.request.query_params.get("vehicle_type")
        is_active = self.request.query_params.get("is_active")

        if vehicle_type:
            queryset = queryset.filter(
                vehicle_type__name__iexact=vehicle_type
            )

        if is_active is not None:
            queryset = queryset.filter(
                is_active=is_active.lower() == "true"
            )

        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsDriverUser()]
        return [IsAuthenticated()]
class VehicleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsDriverUser()]
        return [IsAuthenticated()]
# =========================
# RIDE APIs
# =========================

class RideListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RideSerializer

    def get_queryset(self):
        return Ride.objects.select_related(
            "passenger",
            "driver",
            "vehicle",
            "pickup_location",
            "drop_location",
            "status",
        ).all()

    def get_permissions(self):
        return [IsAuthenticated()]
class RideDetailAPIView(generics.RetrieveAPIView):
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

    queryset = Ride.objects.select_related(
        "passenger",
        "driver",
        "vehicle",
        "pickup_location",
        "drop_location",
        "status",
    )
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vehicle_types(request):
    cache_key = "vehicle_types:active"

    data = cache.get(cache_key)

    if data is not None:
        return success_response(
            data=data,
            message="Vehicle types retrieved successfully.",
        )

    from .models import VehicleType

    data = list(
        VehicleType.objects.filter(
            is_active=True
        ).values(
            "id",
            "name",
        )
    )

    cache.set(cache_key, data, timeout=600)

    return success_response(
        data=data,
        message="Vehicle types retrieved successfully.",
    )

class RideStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        ride_id = kwargs.get("pk")
        new_status = request.data.get("status")

        if not new_status:
            return error_response(
            message="Ride not found.",
            error_code="RIDE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
           )

        try:
            ride = update_ride_status(
                ride_id=ride_id,
                new_status=new_status,
            )

        except Ride.DoesNotExist:
            return error_response(
            message="Ride not found.",
            error_code="RIDE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
           )

        except ValueError as exc:
            return error_response(
            message="Ride not found.",
            error_code="RIDE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
)

        return success_response(
          data=RideSerializer(ride).data,
          message="Ride status updated successfully",
        )
class RideAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ride = accept_ride(pk, request.user)

        except Ride.DoesNotExist:
            return error_response(
             message="Ride not found.",
             error_code="RIDE_NOT_FOUND",
             status_code=status.HTTP_404_NOT_FOUND
           )

        except ValueError as e:
            return error_response(
             message="Ride not found.",
             error_code="RIDE_NOT_FOUND",
             status_code=status.HTTP_404_NOT_FOUND
           )
        return success_response(
           data=RideSerializer(ride).data,
           message="Ride accepted successfully."
         )
class RideCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ride = Ride.objects.get(id=pk)
        except Ride.DoesNotExist:
            return error_response(
             message="Ride not found.",
             error_code="RIDE_NOT_FOUND",
             status_code=status.HTTP_404_NOT_FOUND
            )

        current_status = ride.status.code

        if current_status not in ["REQUESTED", "ACCEPTED"]:
            return error_response(
               message="Ride not found.",
               error_code="RIDE_NOT_FOUND",
               status_code=status.HTTP_404_NOT_FOUND
            )

        cancelled_status = RideStatus.objects.get(code="CANCELLED")

        ride.status = cancelled_status
        ride.save()

        return success_response(
           data=RideSerializer(ride).data,
           message="Ride accepted successfully."
        )
class RideFareAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        distance = request.data.get("distance", 0)
        time = request.data.get("time", 0)
        surge = request.data.get("surge", 0)

        try:
            distance = float(distance)
            time = float(time)
            surge = float(surge)
        except (TypeError, ValueError):
            return error_response(
    message="Username and password are required.",
    error_code="CREDENTIALS_REQUIRED",
    status_code=status.HTTP_400_BAD_REQUEST
)

        fare = calculate_fare(distance, time, surge)

        return success_response(
    data={
        "base_fare": fare["base_fare"],
        "distance_fare": fare["distance_fare"],
        "time_fare": fare["time_fare"],
        "surge": fare["surge"],
        "total": fare["total"],
    },
    message="Fare calculated successfully."
   )
User = get_user_model()


class RegisterAPIView(APIView):

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")

        if not username or not password:
            return error_response(
    message="Username and password are required.",
    error_code="CREDENTIALS_REQUIRED",
    status_code=status.HTTP_400_BAD_REQUEST
)

        if User.objects.filter(username=username).exists():
            return error_response(
    message="Username and password are required.",
    error_code="CREDENTIALS_REQUIRED",
    status_code=status.HTTP_400_BAD_REQUEST
)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return success_response(
    data={
        "id": str(user.pk),
        "username": user.username,
        "email": user.email,
    },
    message="User registered successfully.",
    status_code=status.HTTP_201_CREATED,
)
@api_view(["POST"])
def arrive_ride(request, pk):
    try:
        ride = Ride.objects.get(pk=pk)
    except Ride.DoesNotExist:
        return error_response(
    message="Ride not found.",
    error_code="RIDE_NOT_FOUND",
    status_code=status.HTTP_404_NOT_FOUND,
)

    try:
        arrived_status = RideStatus.objects.get(name="ARRIVED")
    except RideStatus.DoesNotExist:
        return error_response(
    message="ARRIVED status does not exist.",
    error_code="ARRIVED_STATUS_NOT_FOUND",
    status_code=status.HTTP_400_BAD_REQUEST,
)

    ride.status = arrived_status
    ride.save(update_fields=["status"])

    return success_response(
    data={
        "id": str(ride.id),
        "status": arrived_status.name,
    },
    message="Ride marked as arrived successfully.",
)
@api_view(["POST"])
def complete_ride(request, pk):
    try:
        ride = Ride.objects.get(pk=pk)
    except Ride.DoesNotExist:
        return error_response(
    message="Ride not found.",
    error_code="RIDE_NOT_FOUND",
    status_code=status.HTTP_404_NOT_FOUND,
)

    try:
        completed_status = RideStatus.objects.get(name="COMPLETED")
    except RideStatus.DoesNotExist:
        return error_response(
    message="COMPLETED status does not exist.",
    error_code="COMPLETED_STATUS_NOT_FOUND",
    status_code=status.HTTP_400_BAD_REQUEST,
)

    ride.status = completed_status
    ride.save(update_fields=["status"])

    return success_response(
    data={
        "id": str(ride.id),
        "status": completed_status.name,
    },
    message="Ride completed successfully.",
)
class RideViewSet(viewsets.ModelViewSet):

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        ride = get_object_or_404(Ride, pk=pk)

        if ride.status.code != "ACCEPTED":
            return error_response(
    message="Ride must be accepted before starting.",
    error_code="INVALID_RIDE_STATUS",
    status_code=status.HTTP_400_BAD_REQUEST,
)

        started_status = get_object_or_404(
            RideStatus,
            code="STARTED",
            is_active=True,
        )

        ride.status = started_status
        ride.save(update_fields=["status", "updated_at"])

        return success_response(
    data={
        "id": str(ride.id),
        "status": ride.status.code,
    },
    message="Ride started successfully.",
)
# ============================================================
# ADVANCED ORM APIs
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def active_rides(request):
    rides = get_active_rides(request.user)

    return success_response(
    data=list(
        rides.values(
            "id",
            "status__code",
            "driver__id",
            "driver__user__username",
            "vehicle__registration_number",
            "fare",
            "created_at",
        )
    ),
    message="Active rides retrieved successfully.",
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def completed_rides(request):
    rides = get_completed_rides(request.user)

    return success_response(
    data=list(
        rides.values(
            "id",
            "status__code",
            "driver__id",
            "driver__user__username",
            "vehicle__registration_number",
            "fare",
            "created_at",
            "completed_at",
        )
    ),
    message="Completed rides retrieved successfully.",
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cancelled_rides(request):
    rides = get_cancelled_rides(request.user)

    return success_response(
    data=list(
        rides.values(
            "id",
            "status__code",
            "driver__id",
            "driver__user__username",
            "vehicle__registration_number",
            "fare",
            "created_at",
        )
    ),
    message="Cancelled rides retrieved successfully.",
)

@api_view(["GET"])
def driver_ride_history(request):
    rides = get_driver_ride_history(request.user)
    return success_response(
    data=list(
        rides.values(
            "id",
            "status__code",
            "fare",
            "created_at",
        )
    ),
    message="Driver ride history retrieved successfully.",
)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daily_ride_count(request):
    cache_key = "rides:daily_count"

    data = cache.get(cache_key)

    if data is None:
        data = get_daily_ride_count()
        cache.set(cache_key, data, timeout=300)

    return success_response(
    data=data,
    message="Daily ride count retrieved successfully.",
)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def total_completed_rides(request):
    cache_key = "rides:total_completed"

    cached_total = cache.get(cache_key)

    if cached_total is not None:
        return success_response(
    data={
        "total_completed_rides": cached_total,
        "cache": "HIT",
    },
    message="Total completed rides retrieved successfully.",
)

    total = get_total_completed_rides()

    cache.set(cache_key, total, 300)

    return success_response(
    data={
        "total_completed_rides": total,
        "cache": "MISS",
    },
    message="Total completed rides retrieved successfully.",
)
@api_view(["GET"])
def total_fare_earned(request):
    result = get_total_fare_earned(request.user)

    return success_response(
    data=result,
    message="Total fare earned retrieved successfully.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ride_aggregations(request):
    cache_key = "rides:aggregations"

    data = cache.get(cache_key)

    if data is None:
        data = Ride.objects.aggregate(
            total_rides=Count("id"),
            completed_rides=Count(
                "id",
                filter=Q(status__code="COMPLETED")
            ),
            cancelled_rides=Count(
                "id",
                filter=Q(status__code="CANCELLED")
            ),
            total_driver_earnings=Sum(
                "fare",
                filter=Q(status__code="COMPLETED")
            ),
            average_fare=Avg(
                "fare",
                filter=Q(status__code="COMPLETED")
            ),
            maximum_fare=Max(
                "fare",
                filter=Q(status__code="COMPLETED")
            ),
            minimum_fare=Min(
                "fare",
                filter=Q(status__code="COMPLETED")
            ),
        )

        cache.set(cache_key, data, timeout=300)

    return success_response(
    data=data,
    message="Ride aggregations retrieved successfully.",
)
@api_view(["GET"])
def optimized_rides(request):
    rides = Ride.objects.select_related(
        "driver",
        "status",
    ).all()

    data = []

    for ride in rides:
        data.append({
            "id": str(ride.id),
            "driver": str(ride.driver) if ride.driver else None,
            "status": ride.status.code if ride.status else None,
        })

    return success_response(
    data={
        "query_count": len(connection.queries),
        "aggregations": data,
    },
    message="Ride aggregations retrieved successfully.",
)
@api_view(["GET"])
def slow_rides(request):
    rides = Ride.objects.all()

    data = []

    for ride in rides:
        data.append({
            "id": str(ride.id),
            "driver": str(ride.driver) if ride.driver else None,
            "status": ride.status.code if ride.status else None,
        })
    return success_response(
    data={
        "query_count": len(connection.queries),
        "rides": data,
    },
    message="Slow rides retrieved successfully.",
)
class DriverLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            driver = DriverProfile.objects.get(
                user=request.user,
                is_active=True
            )
        except DriverProfile.DoesNotExist:
            return error_response(
    message="Active driver profile not found.",
    error_code="DRIVER_NOT_FOUND",
    status_code=status.HTTP_404_NOT_FOUND
)

        serializer = DriverLocationSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return error_response(
    message="Invalid driver location data.",
    error_code="INVALID_DRIVER_LOCATION",
    status_code=status.HTTP_400_BAD_REQUEST,
    data=serializer.errors
)

        location = (
            Location.objects
           .select_related("driver")
           .filter(driver=driver)
           .order_by("-last_updated")
           .first()
)

        if location:
            location.latitude = serializer.validated_data["latitude"]
            location.longitude = serializer.validated_data["longitude"]

            # Driver sending location means driver is available
            location.is_available = True
            location.availability_status = "ONLINE"

            location.save()
        else:
            location = Location.objects.create(
                driver=driver,
                latitude=serializer.validated_data["latitude"],
                longitude=serializer.validated_data["longitude"],
                is_available=True,
                availability_status="ONLINE",
            )

        return success_response(
    data=DriverLocationSerializer(location).data,
    message="Driver location updated successfully."
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def nearby_drivers(request):
    latitude = request.query_params.get("latitude")
    longitude = request.query_params.get("longitude")
    radius = request.query_params.get("radius")

    if not latitude or not longitude or not radius:
        return error_response(
    message="latitude, longitude and radius are required.",
    error_code="MISSING_LOCATION_PARAMETERS",
    status_code=status.HTTP_400_BAD_REQUEST
)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)
    except ValueError:
        return error_response(
    message="latitude, longitude and radius must be numbers.",
    error_code="INVALID_LOCATION_PARAMETERS",
    status_code=status.HTTP_400_BAD_REQUEST
)
    if latitude < -90 or latitude > 90:
      return error_response(
    message="Invalid latitude. Must be between -90 and 90.",
    error_code="INVALID_LATITUDE",
    status_code=status.HTTP_400_BAD_REQUEST
)

    if longitude < -180 or longitude > 180:
      return error_response(
    message="Invalid radius. Must be greater than 0.",
    error_code="INVALID_RADIUS",
    status_code=status.HTTP_400_BAD_REQUEST
)

    if radius <= 0:
      return error_response(
    message="Invalid radius. Must be greater than 0.",
    error_code="INVALID_RADIUS",
    status_code=status.HTTP_400_BAD_REQUEST
)
    cache_key = f"nearby_drivers:{latitude}:{longitude}:{radius}"

    cached_drivers = cache.get(cache_key)

    if cached_drivers is not None:
       return success_response(
    data=cached_drivers,
    message="Nearby drivers retrieved successfully."
)

    drivers = find_nearby_drivers(
        latitude,
        longitude,
        radius
    )
    cache.set(cache_key, drivers, timeout=60)


    return success_response(
    data=drivers,
    message="Nearby drivers retrieved successfully."
)
class NotificationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by("-created_at")

        paginator = NotificationPagination()
        page = paginator.paginate_queryset(notifications, request)

        serializer = NotificationSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(
                id=pk,
                user=request.user
            )
        except Notification.DoesNotExist:
            return error_response(
    message="Notification not found.",
    error_code="NOTIFICATION_NOT_FOUND",
    status_code=status.HTTP_404_NOT_FOUND
)
        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return success_response(
    data=NotificationSerializer(notification).data,
    message="Notification marked as read successfully."
)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return success_response(
    data={
        "updated_count": updated
    },
    message="All notifications marked as read."
)
# 1. filter()
def filter_rides():
    return Ride.objects.filter(
        status__code="COMPLETED"
    )


# 2. exclude()
def exclude_cancelled_rides():
    return Ride.objects.exclude(
        status__code="CANCELLED"
    )


# 3. Q()
def search_rides():
    return Ride.objects.filter(
        Q(status__code="COMPLETED") |
        Q(status__code="STARTED")
    )


# 4. F()
def rides_fare_check():
    return Ride.objects.filter(
        fare__gt=F("fare")
    )


# 5. annotate()
def rides_with_driver_count():
    return Ride.objects.annotate(
        related_ride_count=Count("driver__rides")
    )


# 6. aggregate()
def ride_fare_statistics():
    return Ride.objects.aggregate(
        total_fare=Sum("fare"),
        average_fare=Avg("fare"),
        maximum_fare=Max("fare"),
        minimum_fare=Min("fare"),
    )


# 7. values()
def ride_values():
    return Ride.objects.values(
        "id",
        "passenger_id",
        "driver_id",
        "status__code",
        "fare",
        "created_at",
    )


# 8. values_list()
def ride_ids():
    return Ride.objects.values_list(
        "id",
        flat=True
    )


# 9. exists()
def has_completed_rides():
    return Ride.objects.filter(
        status__code="COMPLETED"
    ).exists()


# 10. distinct()
def distinct_drivers():
    return Ride.objects.filter(
        driver__isnull=False
    ).values(
        "driver_id"
    ).distinct()
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def advanced_queryset_examples(request):
    from .services.advanced_queries import (
        filter_rides,
        exclude_cancelled_rides,
        search_rides,
        rides_updated_after_created,
        rides_with_driver_count,
        ride_fare_statistics,
        ride_values,
        ride_ids,
        has_completed_rides,
        distinct_drivers,
    )

    return success_response(
    data={
        "filter_count": filter_rides().count(),

        "exclude_cancelled_count":
            exclude_cancelled_rides().count(),

        "q_count":
            search_rides().count(),

        "f_count":
            rides_updated_after_created().count(),

        "annotate_count":
            rides_with_driver_count().count(),

        "aggregate":
            ride_fare_statistics(),

        "values":
            list(ride_values()[:10]),

        "values_list":
            [str(ride_id) for ride_id in ride_ids()[:10]],

        "exists":
            has_completed_rides(),

        "distinct_driver_count":
            distinct_drivers().count(),
    },
    message="Advanced queryset examples retrieved successfully."
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ride_history(request):
    rides = get_ride_history(
        request.user,
        request.query_params
    )

    return success_response(
        data={
        "count": rides.count(),
        "filters": {
            "date": request.query_params.get("date"),
            "status": request.query_params.get("status"),
            "driver": request.query_params.get("driver"),
            "min_fare": request.query_params.get("min_fare"),
            "max_fare": request.query_params.get("max_fare"),
        },
        "data": list(
            rides.values(
                "id",
                "status__code",
                "driver__id",
                "driver__user__username",
                "vehicle__registration_number",
                "fare",
                "created_at",
                "completed_at",
            )
        ),
    })