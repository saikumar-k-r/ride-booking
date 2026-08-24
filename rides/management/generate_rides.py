from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from rides.models import Ride, RideStatus, Location


class Command(BaseCommand):
    help = "Generate test rides"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of rides to create"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]

        # Get or create passenger
        passenger = User.objects.first()

        if not passenger:
            passenger = User.objects.create_user(
                username="testpassenger",
                password="testpassenger123"
            )

        # Get or create ride status
        status, _ = RideStatus.objects.get_or_create(
            code="COMPLETED",
            defaults={
                "name": "Completed",
                "is_active": True
            }
        )

        # Get existing locations or create test locations
        pickup = Location.objects.first()

        if not pickup:
            pickup = Location.objects.create(
                address="Kavali Pickup",
                latitude=14.9167,
                longitude=79.9944,
                is_available=True,
                availability_status="ONLINE"
            )

        drop = Location.objects.exclude(
            id=pickup.id
        ).first()

        if not drop:
            drop = Location.objects.create(
                address="Nellore Drop",
                latitude=14.4426,
                longitude=79.9865,
                is_available=True,
                availability_status="ONLINE"
            )

        # Create rides
        rides = []

        for i in range(count):
            rides.append(
                Ride(
                    passenger=passenger,
                    pickup_location=pickup,
                    drop_location=drop,
                    status=status,
                    fare=100 + (i % 500)
                )
            )

        Ride.objects.bulk_create(
            rides,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {count} rides."
            )
        )