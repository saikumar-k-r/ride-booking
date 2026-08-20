from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .services.ride_service import accept_ride

from .models import Location, RideStatus, DriverProfile,Ride
from .services.fare_service import calculate_fare


class FareCalculationTest(TestCase):

    def test_fare_calculation(self):
        result = calculate_fare(
            distance_km=5,
            duration_minutes=10,
            surge=Decimal("10")
        )

        self.assertEqual(result["base_fare"], Decimal("40"))
        self.assertEqual(result["distance_fare"], Decimal("50"))
        self.assertEqual(result["time_fare"], Decimal("20"))
        self.assertEqual(result["surge"], Decimal("10"))
        self.assertEqual(result["total"], Decimal("120"))
class RideCreationTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="passenger",
            password="testpass123"
        )

        self.pickup = Location.objects.create(
            address="Pickup Location",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
        )

        self.drop = Location.objects.create(
            address="Drop Location",
            latitude=Decimal("12.935200"),
            longitude=Decimal("77.624500"),
        )

        self.requested_status = RideStatus.objects.create(
            code="REQUESTED",
            name="Requested"
        )

        self.client.force_authenticate(user=self.user)

    def test_ride_creation(self):
        response = self.client.post(
            "/api/rides/",
            {
                "passenger": self.user.id,
                "pickup_location": self.pickup.id,
                "drop_location": self.drop.id,
                "status": self.requested_status.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)        


class RideAcceptanceTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.driver_user = User.objects.create_user(
            username="driver_test",
            password="testpass123"
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="TEST-LICENSE-001"
        )

        self.passenger = User.objects.create_user(
            username="passenger_test",
            password="testpass123"
        )

        self.pickup = Location.objects.create(
            address="Pickup Location",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600")
        )

        self.drop = Location.objects.create(
            address="Drop Location",
            latitude=Decimal("12.935200"),
            longitude=Decimal("77.624500")
        )

        self.requested_status = RideStatus.objects.create(
            code="REQUESTED",
            name="Requested"
        )

        self.accepted_status = RideStatus.objects.create(
            code="ACCEPTED",
            name="Accepted"
        )

        self.client.force_authenticate(user=self.driver_user)

    def test_ride_acceptance(self):
        ride = Ride.objects.create(
            passenger=self.passenger,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=self.requested_status,
        )

        accepted_ride = accept_ride(
            ride.id,
            self.driver_user
        )

        self.assertEqual(accepted_ride.driver, self.driver)
        self.assertEqual(accepted_ride.status.code, "ACCEPTED")
    def test_duplicate_ride_acceptance(self):
     ride = Ride.objects.create(
        passenger=self.passenger,
        pickup_location=self.pickup,
        drop_location=self.drop,
        status=self.requested_status,
    )

    # First driver accepts successfully
     accept_ride(ride.id, self.driver_user)

    # Same ride cannot be accepted again
     with self.assertRaises(ValueError):
      accept_ride(ride.id, self.driver_user)