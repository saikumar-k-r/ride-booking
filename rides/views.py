from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .services.fare_service import calculate_fare
from .services.ride_service import accept_ride
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from django.db import connection
from django.db.models import Count, Sum, Avg, Min, Max
from .serializers import DriverLocationSerializer
from rides.services.location_service import find_nearby_drivers

from .permissions import IsAdminUserRole, IsDriverUser
from .models import DriverProfile, Vehicle,Ride,RideStatus,Location
from .serializers import DriverSerializer, VehicleSerializer, RideSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from .services.ride_queries import (
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
    queryset = Ride.objects.all()
    serializer_class = RideSerializer

    def get_permissions(self):
        return [IsAuthenticated()]    
class RideDetailAPIView(generics.RetrieveAPIView):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated] 
class RideStatusAPIView(generics.UpdateAPIView):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        ride = self.get_object()

        current_status = ride.status.code
        new_status = request.data.get("status")

        allowed_transitions = {
            "REQUESTED": ["ACCEPTED", "CANCELLED"],
            "ACCEPTED": ["DRIVER_ARRIVING", "CANCELLED"],
            "DRIVER_ARRIVING": ["STARTED"],
            "STARTED": ["COMPLETED"],
            "COMPLETED": [],
            "CANCELLED": [],
        }

        if new_status not in allowed_transitions.get(current_status, []):
            return Response(
                {
                    "error": f"Invalid transition: {current_status} → {new_status}"
                },
                status=400,
            )

        try:
            new_status_obj = RideStatus.objects.get(code=new_status)
        except RideStatus.DoesNotExist:
            return Response(
                {"error": "Invalid ride status."},
                status=400,
            )

        ride.status = new_status_obj
        ride.save()

        return Response(
            RideSerializer(ride).data,
            status=200
        )  
class RideAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ride = accept_ride(pk, request.user)

        except Ride.DoesNotExist:
            return Response(
                {"detail": "Ride not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            RideSerializer(ride).data,
            status=status.HTTP_200_OK
        )
class RideCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ride = Ride.objects.get(id=pk)
        except Ride.DoesNotExist:
            return Response(
                {"detail": "Ride not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        current_status = ride.status.code

        if current_status not in ["REQUESTED", "ACCEPTED"]:
            return Response(
                {
                    "detail": f"Ride cannot be cancelled from {current_status} status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cancelled_status = RideStatus.objects.get(code="CANCELLED")

        ride.status = cancelled_status
        ride.save()

        return Response(
            RideSerializer(ride).data,
            status=status.HTTP_200_OK
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
            return Response(
                {"detail": "distance, time and surge must be numbers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        fare = calculate_fare(distance, time, surge)

        return Response(
            {
                "base_fare": fare["base_fare"],
                "distance_fare": fare["distance_fare"],
                "time_fare": fare["time_fare"],
                "surge": fare["surge"],
                "total": fare["total"],
            },
            status=status.HTTP_200_OK
        )    
User = get_user_model()


class RegisterAPIView(APIView):

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")

        if not username or not password:
            return Response(
                {"detail": "username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return Response(
            {
                "id": str(user.pk),
                "username": user.username,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED
        )    
@api_view(["POST"])
def arrive_ride(request, pk):
    try:
        ride = Ride.objects.get(pk=pk)
    except Ride.DoesNotExist:
        return Response(
            {"detail": "Ride not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        arrived_status = RideStatus.objects.get(name="ARRIVED")
    except RideStatus.DoesNotExist:
        return Response(
            {"detail": "ARRIVED status does not exist."},
            status=status.HTTP_400_BAD_REQUEST
        )

    ride.status = arrived_status
    ride.save(update_fields=["status"])

    return Response({
        "id": str(ride.id),
        "status": arrived_status.name,
    })
@api_view(["POST"])
def complete_ride(request, pk):
    try:
        ride = Ride.objects.get(pk=pk)
    except Ride.DoesNotExist:
        return Response(
            {"detail": "Ride not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        completed_status = RideStatus.objects.get(name="COMPLETED")
    except RideStatus.DoesNotExist:
        return Response(
            {"detail": "COMPLETED status does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ride.status = completed_status
    ride.save(update_fields=["status"])

    return Response(
        {
            "id": str(ride.id),
            "status": completed_status.name,
        }
    )
class RideViewSet(viewsets.ModelViewSet):

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        ride = get_object_or_404(Ride, pk=pk)

        if ride.status.code != "ACCEPTED":
            return Response(
                {
                    "success": False,
                    "message": "Ride must be accepted before starting",
                    "error_code": "INVALID_RIDE_STATUS",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        started_status = get_object_or_404(
            RideStatus,
            code="STARTED",
            is_active=True,
        )

        ride.status = started_status
        ride.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Ride started successfully",
                "error_code": None,
                "data": {
                    "id": str(ride.id),
                    "status": ride.status.code,
                },
            },
            status=status.HTTP_200_OK,
        )
# ============================================================
# ADVANCED ORM APIs
# ============================================================

@api_view(["GET"])
def active_rides(request):
    rides = get_active_rides(request.user)

    return Response({
        "success": True,
        "count": rides.count(),
        "data": list(
            rides.values(
                "id",
                "status__code",
                "created_at",
            )
        ),
    })


@api_view(["GET"])
def completed_rides(request):
    rides = get_completed_rides()

    return Response({
        "success": True,
        "count": rides.count(),
        "data": list(
            rides.values(
                "id",
                "status__code",
                "fare",
                "created_at",
            )
        ),
    })


@api_view(["GET"])
def cancelled_rides(request):
    rides = get_cancelled_rides()

    return Response({
        "success": True,
        "count": rides.count(),
        "data": list(
            rides.values(
                "id",
                "status__code",
                "created_at",
            )
        ),
    })


@api_view(["GET"])
def driver_ride_history(request):
    rides = get_driver_ride_history(request.user)

    return Response({
        "success": True,
        "count": rides.count(),
        "data": list(
            rides.values(
                "id",
                "status__code",
                "fare",
                "created_at",
            )
        ),
    })


@api_view(["GET"])
def daily_ride_count(request):
    data = get_daily_ride_count()

    return Response({
        "success": True,
        "data": list(data),
    })


@api_view(["GET"])
def total_completed_rides(request):
    total = get_total_completed_rides()

    return Response({
        "success": True,
        "total_completed_rides": total,
    })


@api_view(["GET"])
def total_fare_earned(request):
    result = get_total_fare_earned(request.user)

    return Response({
        "success": True,
        "data": result,
    })    
@api_view(["GET"])
def ride_aggregations(request):
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
        average_fare=Avg("fare"),
        maximum_fare=Max("fare"),
        minimum_fare=Min("fare"),
        total_fare=Sum("fare"),
    )

    return Response({
        "success": True,
        "data": {
            "total_rides": total_rides,
            "completed_rides": completed_rides,
            "cancelled_rides": cancelled_rides,
            "average_fare": fare_data["average_fare"],
            "maximum_fare": fare_data["maximum_fare"],
            "minimum_fare": fare_data["minimum_fare"],
            "total_driver_earnings": fare_data["total_fare"],
        }
    })
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

    return Response({
        "success": True,
        "query_count": len(connection.queries),
        "data": data,
    })
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

    return Response({
        "success": True,
        "query_count": len(connection.queries),
        "data": data,
    })
class DriverLocationAPIView(APIView):

    def post(self, request):
        try:
            driver = DriverProfile.objects.get(user=request.user)
        except DriverProfile.DoesNotExist:
            return Response(
                {"error": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DriverLocationSerializer(data=request.data)

        if serializer.is_valid():
            location = Location.objects.filter(
                driver=driver
            ).order_by("-last_updated").first()

            if location:
                location.latitude = serializer.validated_data["latitude"]
                location.longitude = serializer.validated_data["longitude"]
                location.save()
            else:
                location = Location.objects.create(
                    driver=driver,
                    latitude=serializer.validated_data["latitude"],
                    longitude=serializer.validated_data["longitude"]
                )

            return Response(
                DriverLocationSerializer(location).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
@api_view(["GET"])
def nearby_drivers(request):
    latitude = request.query_params.get("latitude")
    longitude = request.query_params.get("longitude")
    radius = request.query_params.get("radius")

    if not latitude or not longitude or not radius:
        return Response(
            {
                "error": "latitude, longitude and radius are required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)
    except ValueError:
        return Response(
            {"error": "latitude, longitude and radius must be numbers."},
            status=status.HTTP_400_BAD_REQUEST
        )

    drivers = find_nearby_drivers(
        latitude,
        longitude,
        radius
    )

    return Response(
        drivers,
        status=status.HTTP_200_OK
    )    