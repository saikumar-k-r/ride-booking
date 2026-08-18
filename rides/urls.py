from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    DriverListCreateAPIView,
    DriverDetailAPIView,
    VehicleListCreateAPIView,
    VehicleDetailAPIView,
    RideListCreateAPIView,
     RideDetailAPIView,
     RideStatusAPIView,
     RideAcceptAPIView,
     RideCancelAPIView,
     RideFareAPIView,
     RegisterAPIView,
     arrive_ride,
     complete_ride,
     RideViewSet,
     ride_aggregations,
     slow_rides,
     optimized_rides,
      DriverLocationAPIView,
       nearby_drivers,

)

urlpatterns = [
    path(
        "drivers/",
        DriverListCreateAPIView.as_view(),
        name="driver-list-create",
    ),

    path(
        "drivers/<uuid:pk>/",
        DriverDetailAPIView.as_view(),
        name="driver-detail",
    ),

    path(
        "vehicles/",
        VehicleListCreateAPIView.as_view(),
        name="vehicle-list-create",
    ),

    path(
        "vehicles/<uuid:pk>/",
        VehicleDetailAPIView.as_view(),
        name="vehicle-detail",
    ),

    # JWT Authentication
    path(
        "token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "rides/",
         RideListCreateAPIView.as_view(),
         name="ride-list-create",
    ),
    path(
        "rides/<uuid:pk>/",
         RideDetailAPIView.as_view(),
         name="ride-detail",
    ),
    path(
        "rides/<uuid:pk>/status/",
         RideStatusAPIView.as_view(),
         name="ride-status",
    ),
    path(
        "rides/<uuid:pk>/accept/",
         RideAcceptAPIView.as_view(),
        name="ride-accept",
    ),
    path(
        "rides/<uuid:pk>/cancel/",
         RideCancelAPIView.as_view(),
         name="ride-cancel",
    ),
    path(
       "rides/<uuid:pk>/fare/",
        RideFareAPIView.as_view(),
        name="ride-fare",
    ),
   path(
        "register/",
        RegisterAPIView.as_view(),
        name="register",
    ),

    path(
    "rides/<uuid:pk>/start/",
    RideViewSet.as_view({"post": "start"}),
    name="ride-start",
),

path(
    "rides/<uuid:pk>/arrive/",
    arrive_ride,
    name="ride-arrive",
),

path(
    "rides/<uuid:pk>/complete/",
    complete_ride,
    name="ride-complete",
),
path(
    "ride-aggregations/",
    ride_aggregations,
    name="ride-aggregations"
),
path("slow-rides/", slow_rides, name="slow-rides"),
path("optimized-rides/", optimized_rides, name="optimized-rides"),
path(
    "drivers/location/",
    DriverLocationAPIView.as_view(),
    name="driver-location",
),
path(
    "drivers/nearby/",
    nearby_drivers,
    name="nearby-drivers",
),
]