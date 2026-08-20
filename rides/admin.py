from django.contrib import admin
from .models import (
    VehicleType,
    DriverProfile,
    Vehicle,
    Location,
    RideStatus,
    Ride,
)


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "license_number", "is_verified", "is_active", "created_at")
    search_fields = ("user__username", "license_number")
    list_filter = ("is_verified", "is_active")
    ordering = ("-created_at",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "driver",
        "vehicle_type",
        "model_name",
        "is_active",
        "created_at",
    )
    search_fields = (
        "registration_number",
        "model_name",
        "driver__user__username",
    )
    list_filter = ("vehicle_type", "is_active")
    ordering = ("registration_number",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("address", "latitude", "longitude", "created_at")
    search_fields = ("address",)
    ordering = ("-created_at",)


@admin.register(RideStatus)
class RideStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    search_fields = ("name", "code")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "passenger",
        "driver",
        "vehicle",
        "status",
        "fare",
        "requested_at",
        "completed_at",
    )
    search_fields = (
        "passenger__username",
        "driver__user__username",
        "vehicle__registration_number",
    )
    list_filter = ("status", "requested_at")
    ordering = ("-requested_at",)