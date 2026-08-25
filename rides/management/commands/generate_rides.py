import random
import uuid

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from rides.models import DriverProfile, Location


class Command(BaseCommand):
    help = "Generate test drivers and locations for performance testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=1000,
            help="Number of test drivers to create",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]

        User = get_user_model()

        users = []
        for _ in range(count):
            unique_id = uuid.uuid4().hex[:12]

            users.append(
                User(
                    username=f"test_driver_{unique_id}",
                    email=f"test_driver_{unique_id}@example.com",
                    is_active=True,
                )
            )

        User.objects.bulk_create(users)

        drivers = []

        for user in users:
            drivers.append(
                DriverProfile(
                    user=user,
                    license_number=f"TEST-{uuid.uuid4().hex[:12].upper()}",
                    is_verified=True,
                    is_active=True,
                )
            )

        DriverProfile.objects.bulk_create(drivers)

        locations = []

        base_latitude = 17.3850
        base_longitude = 78.4867

        for driver in drivers:
            latitude = base_latitude + random.uniform(-0.05, 0.05)
            longitude = base_longitude + random.uniform(-0.05, 0.05)

            locations.append(
                Location(
                    driver=driver,
                    address="Test Location Hyderabad",
                    latitude=latitude,
                    longitude=longitude,
                    is_available=True,
                    availability_status="ONLINE",
                )
            )

        Location.objects.bulk_create(locations)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {count} test drivers and locations."
            )
        )