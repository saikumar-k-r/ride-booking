from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DriverProfile, Vehicle, Ride,Location

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
class RideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = "__all__"    
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