def validate_location(latitude, longitude, radius=None):
    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if radius is not None:
            radius = float(radius)

    except (TypeError, ValueError):
        raise ValueError(
            "Latitude and longitude must be valid numbers."
        )

    if not -90 <= latitude <= 90:
        raise ValueError(
            "Invalid latitude. Must be between -90 and 90."
        )

    if not -180 <= longitude <= 180:
        raise ValueError(
            "Invalid longitude. Must be between -180 and 180."
        )

    if radius is not None and radius <= 0:
        raise ValueError(
            "Radius must be greater than 0."
        )

    return latitude, longitude, radius