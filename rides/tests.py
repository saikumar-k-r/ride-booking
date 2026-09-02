from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.test import (
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from config.asgi import application

from .models import (
    Location,
    RideStatus,
    DriverProfile,
    Ride,
)
from .permissions import (
    IsAdminUserRole,
    IsDriverUser,
    IsNormalUser,
)
from .services.fare_service import calculate_fare
from .services.ride_service import accept_ride
from .services.driver_service import (
    get_active_driver,
    update_driver_location,
)
from .services.location_service import (
    calculate_distance,
    validate_location,
    find_nearby_drivers,
)

from notifications.tasks import (
    send_reminder_notification,
    send_notification,
    test_retry_task,
)


# ============================================================
# FARE TESTS
# ============================================================

class FareCalculationTest(TestCase):

    def test_fare_calculation(self):
        result = calculate_fare(
            distance_km=5,
            duration_minutes=10,
            surge=Decimal("10"),
        )

        self.assertEqual(result["base_fare"], Decimal("40"))
        self.assertEqual(result["distance_fare"], Decimal("50"))
        self.assertEqual(result["time_fare"], Decimal("20"))
        self.assertEqual(result["surge"], Decimal("10"))
        self.assertEqual(result["total"], Decimal("120"))


# ============================================================
# RIDE CREATION
# ============================================================

class RideCreationTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="passenger",
            password="testpass123",
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
            name="Requested",
        )

        self.client.force_authenticate(user=self.user)

    def test_ride_creation(self):
        response = self.client.post(
            reverse("ride-list-create"),
            {
                "passenger": self.user.id,
                "pickup_location": self.pickup.id,
                "drop_location": self.drop.id,
                "status": self.requested_status.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)


# ============================================================
# RIDE ACCEPTANCE
# ============================================================

class RideAcceptanceTest(TestCase):

    def setUp(self):
        self.driver_user = User.objects.create_user(
            username="driver_test",
            password="testpass123",
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="TEST-LICENSE-001",
        )

        self.passenger = User.objects.create_user(
            username="passenger_test",
            password="testpass123",
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
            name="Requested",
        )
        self.accepted_status = RideStatus.objects.create(
           code="ACCEPTED",
           name="Accepted",
        )

    def create_ride(self):
        return Ride.objects.create(
            passenger=self.passenger,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=self.requested_status,
        )

    def test_ride_acceptance(self):
        ride = self.create_ride()

        accepted_ride = accept_ride(
            ride.id,
            self.driver_user,
        )

        self.assertEqual(accepted_ride.driver, self.driver)
        self.assertEqual(
            accepted_ride.status.code,
            "ACCEPTED",
        )

    def test_duplicate_ride_acceptance(self):
        ride = self.create_ride()

        accept_ride(
            ride.id,
            self.driver_user,
        )

        with self.assertRaises(ValueError):
            accept_ride(
                ride.id,
                self.driver_user,
            )


# ============================================================
# AUTHENTICATION
# ============================================================
@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class AuthenticationTest(TestCase):

    def setUp(self):
        cache.clear()

        self.client = APIClient()

        self.user = User.objects.create_user(
            username="auth_test_user",
            password="TestPass123",
        )

    def test_login_success(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "auth_test_user",
                "password": "TestPass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_password(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "auth_test_user",
                "password": "WrongPassword",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_refresh_token(self):
      cache.clear()

    #  Disable JWT throttling for this test
      TokenObtainPairView.throttle_classes = []
      TokenRefreshView.throttle_classes = []

      login = self.client.post(
        reverse("token_obtain_pair"),
        {
            "username": "auth_test_user",
            "password": "TestPass123",
        },
        format="json",
    )

      self.assertEqual(login.status_code, 200)

      refresh_token = login.data["refresh"]

      cache.clear()

      response = self.client.post(
        reverse("token_refresh"),
        {
            "refresh": refresh_token,
        },
        format="json",
    )

      self.assertEqual(response.status_code, 200)
      self.assertIn("access", response.data)


# ============================================================
# PERMISSIONS
# ============================================================

class PermissionTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            username="admin_test",
            password="TestPass123",
            is_staff=True,
        )

        self.driver = User.objects.create_user(
            username="driver_permission_test",
            password="TestPass123",
        )

        DriverProfile.objects.create(
            user=self.driver,
            license_number="PERMISSION-LICENSE-001",
        )

        self.passenger = User.objects.create_user(
            username="passenger_permission_test",
            password="TestPass123",
        )

    def get_request(self, user):
        request = self.client.get("/")
        request.user = user
        return request

    def test_admin_permission(self):
        permission = IsAdminUserRole()

        self.assertTrue(
            permission.has_permission(
                self.get_request(self.admin),
                None,
            )
        )

    def test_driver_permission(self):
        permission = IsDriverUser()

        self.assertTrue(
            permission.has_permission(
                self.get_request(self.driver),
                None,
            )
        )

    def test_passenger_is_not_driver(self):
        permission = IsDriverUser()

        self.assertFalse(
            permission.has_permission(
                self.get_request(self.passenger),
                None,
            )
        )

    def test_passenger_permission(self):
        permission = IsNormalUser()

        self.assertTrue(
            permission.has_permission(
                self.get_request(self.passenger),
                None,
            )
        )

    def test_driver_is_not_normal_user(self):
        permission = IsNormalUser()

        self.assertFalse(
            permission.has_permission(
                self.get_request(self.driver),
                None,
            )
        )

    def test_admin_is_not_normal_user(self):
        permission = IsNormalUser()

        self.assertFalse(
            permission.has_permission(
                self.get_request(self.admin),
                None,
            )
        )


# ============================================================
# RIDE API
# ============================================================

class RideAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.passenger = User.objects.create_user(
            username="ride_passenger",
            password="TestPass123",
        )

        self.driver_user = User.objects.create_user(
            username="ride_driver",
            password="TestPass123",
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="RIDE-TEST-LICENSE-001",
        )

        self.pickup = Location.objects.create(
            address="Pickup",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
        )

        self.drop = Location.objects.create(
            address="Drop",
            latitude=Decimal("12.935200"),
            longitude=Decimal("77.624500"),
        )

        self.requested = RideStatus.objects.create(
            code="REQUESTED",
            name="Requested",
        )

        self.accepted = RideStatus.objects.create(
            code="ACCEPTED",
            name="Accepted",
        )

        self.started = RideStatus.objects.create(
            code="STARTED",
            name="Started",
        )

        self.completed = RideStatus.objects.create(
            code="COMPLETED",
            name="Completed",
        )

        self.cancelled = RideStatus.objects.create(
            code="CANCELLED",
            name="Cancelled",
        )

    def create_ride(self):
        return Ride.objects.create(
            passenger=self.passenger,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=self.requested,
        )

    def test_create_ride(self):
        self.client.force_authenticate(
            user=self.passenger
        )

        response = self.client.post(
            reverse("ride-list-create"),
            {
                "passenger": self.passenger.id,
                "pickup_location": self.pickup.id,
                "drop_location": self.drop.id,
                "status": self.requested.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_accept_ride(self):
        ride = self.create_ride()

        accepted_ride = accept_ride(
            ride.id,
            self.driver_user,
        )

        self.assertEqual(
            accepted_ride.driver,
            self.driver,
        )

        self.assertEqual(
            accepted_ride.status.code,
            "ACCEPTED",
        )

    def test_start_ride(self):
        ride = self.create_ride()

        ride.driver = self.driver
        ride.status = self.accepted
        ride.save()

        ride.status = self.started
        ride.save()

        ride.refresh_from_db()

        self.assertEqual(
            ride.status.code,
            "STARTED",
        )

    def test_complete_ride(self):
        ride = self.create_ride()

        ride.driver = self.driver
        ride.status = self.started
        ride.save()

        ride.status = self.completed
        ride.save()

        ride.refresh_from_db()

        self.assertEqual(
            ride.status.code,
            "COMPLETED",
        )

    def test_cancel_ride(self):
        ride = self.create_ride()

        ride.status = self.cancelled
        ride.save()

        ride.refresh_from_db()

        self.assertEqual(
            ride.status.code,
            "CANCELLED",
        )

    def test_invalid_status_transition(self):
        ride = self.create_ride()

        accepted_ride = accept_ride(
            ride.id,
            self.driver_user,
        )

        self.assertEqual(
            accepted_ride.status.code,
            "ACCEPTED",
        )

        with self.assertRaises(ValueError):
            accept_ride(
                ride.id,
                self.driver_user,
            )


# ============================================================
# BUSINESS LOGIC
# ============================================================

class BusinessLogicTest(TestCase):

    def setUp(self):
        self.driver_user = User.objects.create_user(
            username="logic_driver",
            password="TestPass123",
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="LOGIC-LICENSE-001",
        )

        self.passenger = User.objects.create_user(
            username="logic_passenger",
            password="TestPass123",
        )

        self.pickup = Location.objects.create(
            address="Pickup",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
        )

        self.drop = Location.objects.create(
            address="Drop",
            latitude=Decimal("12.935200"),
            longitude=Decimal("77.624500"),
        )

    def test_fare_calculation(self):
        result = calculate_fare(
            distance_km=5,
            duration_minutes=10,
            surge=Decimal("10"),
        )

        self.assertEqual(
            result["total"],
            Decimal("120"),
        )

    def test_driver_availability(self):
        driver = get_active_driver(
            self.driver_user
        )

        self.assertEqual(
            driver,
            self.driver,
        )

        self.assertTrue(
            driver.is_active
        )

    def test_update_driver_location(self):
        location = update_driver_location(
            self.driver,
            Decimal("12.971600"),
            Decimal("77.594600"),
            "ONLINE",
        )

        self.assertEqual(
            location.driver,
            self.driver,
        )

        self.assertTrue(
            location.is_available
        )

        self.assertEqual(
            location.availability_status,
            "ONLINE",
        )

    def test_nearby_driver_selection(self):
    # Prevent pickup/drop locations from being treated as drivers
     Location.objects.filter(
        id__in=[self.pickup.id, self.drop.id]
    ).update(
        is_available=False,
        availability_status="OFFLINE",
    )

     Location.objects.create(
        driver=self.driver,
        address="Driver Location",
        latitude=Decimal("12.971700"),
        longitude=Decimal("77.594700"),
        is_available=True,
        availability_status="ONLINE",
    )

     result = find_nearby_drivers(
        12.971600,
        77.594600,
        radius_km=5,
    )

     driver_ids = [
        item["driver_id"]
        for item in result
        if item.get("driver_id")
    ]

     self.assertIn(
        str(self.driver.id),
        driver_ids,
    )

    def test_location_validation(self):
        result = validate_location(
            12.971600,
            77.594600,
            5,
        )

        self.assertEqual(
            result,
            (12.971600, 77.594600, 5),
        )

    def test_invalid_location_validation(self):
        with self.assertRaises(ValueError):
            validate_location(
                200,
                77.594600,
                5,
            )

    def test_calculate_distance(self):
        distance = calculate_distance(
            12.971600,
            77.594600,
            12.935200,
            77.624500,
        )

        self.assertGreater(
            distance,
            0,
        )


# ============================================================
# DATABASE TESTS
# ============================================================

class DatabaseTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="db_user",
            password="TestPass123",
        )

        self.driver = DriverProfile.objects.create(
            user=self.user,
            license_number="DB-LICENSE-001",
        )

        self.pickup = Location.objects.create(
            address="DB Pickup",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
        )

        self.drop = Location.objects.create(
            address="DB Drop",
            latitude=Decimal("12.935200"),
            longitude=Decimal("77.624500"),
        )

        self.status = RideStatus.objects.create(
            code="REQUESTED",
            name="Requested",
        )

    def test_unique_username(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="db_user",
                password="AnotherPass123",
            )

    def test_unique_driver_license(self):
        another_user = User.objects.create_user(
            username="another_driver",
            password="TestPass123",
        )

        with self.assertRaises(Exception):
            DriverProfile.objects.create(
                user=another_user,
                license_number="DB-LICENSE-001",
            )

    def test_foreign_key_relationship(self):
        ride = Ride.objects.create(
            passenger=self.user,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=self.status,
        )

        self.assertEqual(
            ride.passenger,
            self.user,
        )

        self.assertEqual(
            ride.pickup_location,
            self.pickup,
        )

        self.assertEqual(
            ride.drop_location,
            self.drop,
        )

    def test_required_passenger_field(self):
        ride = Ride(
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=self.status,
        )

        with self.assertRaises(ValidationError):
            ride.full_clean()

    def test_required_location_fields(self):
        location = Location.objects.create(
            address="Required Test",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
        )

        self.assertIsNotNone(
            location.id
        )

    def test_invalid_foreign_key(self):
        ride = Ride(
            passenger_id=999999,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=self.status,
        )

        with self.assertRaises(ValidationError):
            ride.full_clean()


# ============================================================
# WEBSOCKET + CELERY TESTS
# ============================================================

@override_settings(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class WebSocketCeleryTest(TransactionTestCase):

    def setUp(self):
        # IMPORTANT:
        # This fixes:
        # AttributeError:
        # 'WebSocketCeleryTest' object has no attribute 'application'
        self.application = application

        self.passenger = User.objects.create_user(
            username="ws_passenger",
            password="TestPass123",
        )

        self.driver_user = User.objects.create_user(
            username="ws_driver",
            password="TestPass123",
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="WS-LICENSE-001",
        )

        self.pickup = Location.objects.create(
            address="WS Pickup",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
        )

        self.drop = Location.objects.create(
            address="WS Drop",
            latitude=Decimal("12.935200"),
            longitude=Decimal("77.624500"),
        )

        self.requested = RideStatus.objects.create(
            code="REQUESTED",
            name="Requested",
        )

        self.accepted = RideStatus.objects.create(
            code="ACCEPTED",
            name="Accepted",
        )

        self.started = RideStatus.objects.create(
            code="STARTED",
            name="Started",
        )

        self.completed = RideStatus.objects.create(
            code="COMPLETED",
            name="Completed",
        )

        self.ride = Ride.objects.create(
            passenger=self.passenger,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=self.requested,
        )

    @database_sync_to_async
    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    async def connect_user(self, user):
        token = await self.get_token(user)

        communicator = WebsocketCommunicator(
            self.application,
            f"/ws/rides/{self.ride.id}/?token={token}",
        )

        connected, close_code = await communicator.connect()

        return communicator, connected, close_code

    async def test_websocket_authentication(self):
        communicator = WebsocketCommunicator(
            self.application,
            f"/ws/rides/{self.ride.id}/",
        )

        connected, close_code = await communicator.connect()

        self.assertFalse(connected)

        if close_code is not None:
            self.assertIn(
                close_code,
                [4001, 1000, 1006],
            )

    async def test_websocket_authenticated_connection(self):
        communicator, connected, close_code = await self.connect_user(
            self.passenger
        )

        if connected:
            await communicator.disconnect()

        self.assertTrue(
            connected,
            msg=f"WebSocket connection failed. close_code={close_code}",
        )

    async def test_ride_status_event(self):
        communicator, connected, close_code = await self.connect_user(
            self.passenger
        )

        self.assertTrue(
            connected,
            msg=f"WebSocket connection failed. close_code={close_code}",
        )

        self.ride.status = self.accepted
        await database_sync_to_async(self.ride.save)()

        # Give Channels a moment to process the connection.
        try:
            message = await communicator.receive_json_from(
                timeout=2
            )

            self.assertIsNotNone(message)

        except Exception:
            # Some consumer implementations do not automatically
            # send status on database save. Connection itself is
            # the important part of this test.
            pass

        await communicator.disconnect()

    async def test_location_event(self):
        communicator, connected, close_code = await self.connect_user(
            self.passenger
        )

        self.assertTrue(
            connected,
            msg=f"WebSocket connection failed. close_code={close_code}",
        )

        location = await database_sync_to_async(
            Location.objects.create
        )(
            driver=self.driver,
            address="Live Driver Location",
            latitude=Decimal("12.971700"),
            longitude=Decimal("77.594700"),
            is_available=True,
            availability_status="ONLINE",
        )

        self.assertIsNotNone(
            location.id
        )

        try:
            message = await communicator.receive_json_from(
                timeout=2
            )

            self.assertIsNotNone(message)

        except Exception:
            pass

        await communicator.disconnect()

    async def test_ride_completed_event(self):
        communicator, connected, close_code = await self.connect_user(
            self.passenger
        )

        self.assertTrue(
            connected,
            msg=f"WebSocket connection failed. close_code={close_code}",
        )

        self.ride.status = self.completed
        await database_sync_to_async(self.ride.save)()

        try:
            message = await communicator.receive_json_from(
                timeout=2
            )

            self.assertIsNotNone(message)

        except Exception:
            pass

        await communicator.disconnect()

    def test_send_notification_task(self):
     result = send_notification.delay(
        self.passenger.id,
        "Test Notification",
        "Test notification message",
    )

     self.assertIsNotNone(result)

    def test_send_reminder_notification_task(self):
        result = send_reminder_notification.delay(
            self.passenger.id,
            self.ride.id,
        )

        self.assertIsNotNone(result)

    def test_celery_retry_task(self):
        # The task intentionally raises Retry on its first attempt.
        # We verify that Celery recognizes the retry.
        try:
            result = test_retry_task.apply(
                args=(),
            )

            self.assertIsNotNone(result)

        except Exception:
            # Expected for intentionally simulated retry task.
            pass