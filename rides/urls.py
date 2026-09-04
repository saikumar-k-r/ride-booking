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
       NotificationListView,
    NotificationReadView,
    NotificationReadAllView,
    advanced_queryset_examples,
    ride_history,
    active_rides,
    completed_rides,
    cancelled_rides,
    total_completed_rides,
    vehicle_types,

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
    "auth/token/",
    TokenObtainPairView.as_view(),
    name="token_obtain_pair",
),

path(
    "auth/token/refresh/",
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
    "vehicle-types/",
     vehicle_types,
    name="vehicle-types",
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
    "auth/register/",
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
path(
    "notifications/",
    NotificationListView.as_view(),
    name="notifications",
),

path(
    "notifications/<uuid:pk>/read/",
    NotificationReadView.as_view(),
    name="notification-read",
),

path(
    "notifications/read-all/",
    NotificationReadAllView.as_view(),
    name="notifications-read-all",
),
path(
    "advanced-querysets/",
    advanced_queryset_examples,
    name="advanced-querysets"
),
 path("rides/history/", ride_history, name="ride-history"),
path("rides/active/", active_rides, name="active-rides"),
path("rides/completed/", completed_rides, name="completed-rides"),
path("rides/cancelled/", cancelled_rides, name="cancelled-rides"),
path(
        "total-completed-rides/",
        total_completed_rides,
        name="total-completed-rides"
    ),

]