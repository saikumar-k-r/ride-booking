from django.db import connection
from django.core.cache import cache
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({
        "success": True,
        "status": "healthy",
    })


def database_health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse({
            "success": True,
            "status": "healthy",
            "database": "available",
        })
    except Exception:
        return JsonResponse({
            "success": False,
            "status": "unhealthy",
            "database": "unavailable",
        }, status=503)


def redis_health(request):
    try:
        cache.set("health_check", "ok", timeout=10)
        value = cache.get("health_check")

        if value != "ok":
            raise RuntimeError("Redis check failed")

        return JsonResponse({
            "success": True,
            "status": "healthy",
            "redis": "available",
        })
    except Exception:
        return JsonResponse({
            "success": False,
            "status": "unhealthy",
            "redis": "unavailable",
        }, status=503)