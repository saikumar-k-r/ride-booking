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



class IsOwnerOrAdmin(BasePermission):
    """
    Allows access only to the resource owner or an admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        owner = getattr(obj, "passenger", None)

        if owner is None:
            owner = getattr(obj, "user", None)

        return owner == request.user
class IsDriverOwnerOrAdmin(BasePermission):
    """
    Allows access only to the driver owner or an admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        driver = getattr(obj, "driver", None)

        if driver is None:
            driver = getattr(obj, "driver_profile", None)

        return driver is not None and driver.user == request.user
class IsRideOwnerOrDriverOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if obj.passenger == request.user:
            return True

        driver = getattr(obj, "driver", None)
        return driver is not None and driver.user == request.user