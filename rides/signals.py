from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import VehicleType


@receiver(post_save, sender=VehicleType)
def invalidate_vehicle_type_cache_on_save(sender, instance, **kwargs):
    cache.delete("vehicle_types:active")


@receiver(post_delete, sender=VehicleType)
def invalidate_vehicle_type_cache_on_delete(sender, instance, **kwargs):
    cache.delete("vehicle_types:active")