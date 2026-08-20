from decimal import Decimal


BASE_FARE = Decimal("40")
PER_KM_RATE = Decimal("10")
PER_MINUTE_RATE = Decimal("2")
SURGE_RATE = Decimal("10")


def calculate_fare(distance_km, duration_minutes, surge=Decimal("0")):
    distance_fare = Decimal(str(distance_km)) * PER_KM_RATE
    time_fare = Decimal(str(duration_minutes)) * PER_MINUTE_RATE

    total = (
        BASE_FARE
        + distance_fare
        + time_fare
        + Decimal(str(surge))
    )

    return {
        "base_fare": BASE_FARE,
        "distance_fare": distance_fare,
        "time_fare": time_fare,
        "surge": Decimal(str(surge)),
        "total": total,
    }
