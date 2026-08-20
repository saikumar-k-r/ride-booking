from math import radians, sin, cos, sqrt, atan2
from rides.models import Location


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers.
    """

    earth_radius = 6371.0

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c
def find_nearby_drivers(latitude, longitude, radius_km=5):
    nearby_drivers = []

    locations = Location.objects.filter(
       availability_status="ONLINE"
    )

    for location in locations:
        distance = calculate_distance(
            latitude,
            longitude,
            location.latitude,
            location.longitude
        )

        if distance <= radius_km:
            nearby_drivers.append({
                "driver_id": str(location.driver.id),
                "latitude": location.latitude,
                "longitude": location.longitude,
                "distance_km": round(distance, 2),
            })

    nearby_drivers.sort(key=lambda x: x["distance_km"])

    return nearby_drivers