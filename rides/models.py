import uuid

from django.db import models
from django.contrib.auth.models import User

class VehicleType(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=50,
        unique=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name
class DriverProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="driver_profile"
    )

    license_number = models.CharField(
        max_length=50,
        unique=True
    )

    is_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["license_number"]),
            models.Index(fields=["is_verified", "is_active"]),
        ]

    def _str_(self):
        return f"Driver: {self.user.username}"
class Vehicle(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="vehicles"
    )

    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name="vehicles_records"
    )

    registration_number = models.CharField(
        max_length=20,
        unique=True
    )

    model_name = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["registration_number"]
        indexes = [
            models.Index(fields=["driver"]),
            models.Index(fields=["vehicle_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.registration_number
class Location(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    driver = models.ForeignKey(
    DriverProfile,
    on_delete=models.CASCADE,
    related_name="locations",
    null=True,
    blank=True,
    )

    address = models.CharField(max_length=255)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    is_available = models.BooleanField(default=True)

    availability_status = models.CharField(
      max_length=10,
      choices=[
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
        ("BUSY", "Busy"),
    ],
      default="ONLINE"
    )

    class Meta:
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return self.address
class RideStatus(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
class Ride(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rides"
    )

    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rides"
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rides"
    )

    pickup_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="pickup_rides"
    )

    drop_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="drop_rides"
    )

    status = models.ForeignKey(
        RideStatus,
        on_delete=models.PROTECT,
        related_name="rides"
    )

    fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    requested_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
         indexes = [
            models.Index(fields=["passenger", "status"]),
            models.Index(fields=["driver", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]
    def __str__(self):
        return str(self.id)   
