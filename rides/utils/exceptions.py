class RideServiceError(Exception):
    """Base exception for ride service errors."""


class RideNotFoundError(RideServiceError):
    """Raised when a ride does not exist."""


class RideStatusError(RideServiceError):
    """Raised when a ride status transition is invalid."""


class DriverNotFoundError(RideServiceError):
    """Raised when a driver profile does not exist."""
