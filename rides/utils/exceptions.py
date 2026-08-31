class RideServiceError(Exception):
    """Base exception for ride service errors."""
    pass


class RideNotFoundError(RideServiceError):
    """Raised when a ride does not exist."""
    pass


class RideStatusError(RideServiceError):
    """Raised when a ride status transition is invalid."""
    pass


class DriverNotFoundError(RideServiceError):
    """Raised when a driver profile does not exist."""
    pass