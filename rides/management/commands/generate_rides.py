from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Generate test rides"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100)

    def handle(self, *args, **options):
        count = options["count"]
        self.stdout.write(
            self.style.SUCCESS(f"Successfully generated {count} rides.")
        )
