from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    """
    Admin users can manage all drivers and vehicles.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsDriverUser(BasePermission):
    """
    Driver users are users who have a DriverProfile.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return hasattr(request.user, "driver_profile")


class IsNormalUser(BasePermission):
    """
    Authenticated users who are not admins and not drivers.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return (
            not request.user.is_staff
            and not request.user.is_superuser
            and not hasattr(request.user, "driver_profile")
        )
    