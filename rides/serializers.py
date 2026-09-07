from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DriverProfile, Vehicle, Ride,Location,Notification,RideStatus

class DriverSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    vehicle = serializers.SerializerMethodField()

    def get_vehicle(self, obj):
      vehicle = Vehicle.objects.filter(driver=obj).first()

      if not vehicle:
        return None

      return {
        "type": vehicle.vehicle_type.name,
        "registration_number": vehicle.registration_number,
    }

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "user",
            "username",
            "license_number",
            "is_verified",
            "is_active",
            "created_at",
            "updated_at",
            "vehicle",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "created_at",
            "updated_at",
        ]

    def validate_license_number(self, value):
     value = value.strip().upper()

     if not value:
        raise serializers.ValidationError(
            "License number is required."
        )

     queryset = DriverProfile.objects.filter(
        license_number=value
    )

     if self.instance:
        queryset = queryset.exclude(pk=self.instance.pk)

     if queryset.exists():
        raise serializers.ValidationError(
            "Driver with this license number already exists."
        )

     return value


    def validate_user(self, value):
     queryset = DriverProfile.objects.filter(user=value)

     if self.instance:
        queryset = queryset.exclude(pk=self.instance.pk)

     if queryset.exists():
        raise serializers.ValidationError(
            "This user is already registered as a driver."
        )

     return value



class VehicleSerializer(serializers.ModelSerializer):

    driver_name = serializers.CharField(
        source="driver.user.username",
        read_only=True
    )

    vehicle_type_name = serializers.CharField(
        source="vehicle_type.name",
        read_only=True
    )

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "driver",
            "driver_name",
            "vehicle_type",
            "vehicle_type_name",
            "registration_number",
            "model_name",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "driver_name",
            "vehicle_type_name",
            "created_at",
            "updated_at",
        ]

    def validate_registration_number(self, value):
        value = value.strip().upper()

        queryset = Vehicle.objects.filter(
            registration_number=value
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "Vehicle with this registration number already exists."
            )

        return value

    def validate_driver(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Driver is not active."
            )

        return value

    def validate_vehicle_type(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Vehicle type is not active."
            )

        return value
class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = ["id", "username", "email"]


class DriverSummarySerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "username",
            "license_number",
            "is_verified",
            "is_active",
        ]
        read_only_fields = fields


class VehicleSummarySerializer(serializers.ModelSerializer):
    vehicle_type_name = serializers.CharField(
        source="vehicle_type.name",
        read_only=True
    )

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "registration_number",
            "model_name",
            "vehicle_type_name",
            "is_active",
        ]
        read_only_fields = fields


class LocationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "address",
            "latitude",
            "longitude",
            "is_available",
            "availability_status",
        ]
        read_only_fields = fields


class RideStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideStatus
        fields = ["id", "code", "name"]
        read_only_fields = fields


class RideSerializer(serializers.ModelSerializer):
    passenger_details = UserSummarySerializer(
        source="passenger",
        read_only=True
    )

    driver_details = DriverSummarySerializer(
        source="driver",
        read_only=True
    )

    vehicle_details = VehicleSummarySerializer(
        source="vehicle",
        read_only=True
    )

    pickup_details = LocationSummarySerializer(
        source="pickup_location",
        read_only=True
    )

    drop_details = LocationSummarySerializer(
        source="drop_location",
        read_only=True
    )

    status_details = RideStatusSerializer(
        source="status",
        read_only=True
    )

    class Meta:
        model = Ride
        fields = [
            "id",
            "passenger",
            "passenger_details",
            "driver",
            "driver_details",
            "vehicle",
            "vehicle_details",
            "pickup_location",
            "pickup_details",
            "drop_location",
            "drop_details",
            "status",
            "status_details",
            "fare",
            "requested_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "passenger_details",
            "driver_details",
            "vehicle_details",
            "pickup_details",
            "drop_details",
            "status_details",
            "requested_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

        if fields:
            allowed = set(fields)
            existing = set(self.fields)

            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def validate_fare(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Fare cannot be negative."
            )
        return value
class RideCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = [
            "passenger",
            "driver",
            "vehicle",
            "pickup_location",
            "drop_location",
            "status",
            "fare",
        ]

    def validate_fare(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Fare cannot be negative."
            )
        return value

    def validate(self, attrs):
        pickup = attrs.get("pickup_location")
        drop = attrs.get("drop_location")

        if pickup and drop and pickup == drop:
            raise serializers.ValidationError(
                "Pickup and drop locations must be different."
            )

        return attrs
class DriverLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "latitude",
            "longitude",
            "last_updated",
            "is_available",
        ]
        read_only_fields = ["id", "last_updated"]
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "title",
            "message",
            "notification_type",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]