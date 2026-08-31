from rest_framework.response import Response


def decimal_to_float(value):
    if value is None:
        return None

    return float(value)


def success_response(
    data=None,
    message="Success",
    status_code=200
):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(
    message="Something went wrong.",
    error_code="ERROR",
    data=None,
    status_code=400
):
    return Response(
        {
            "success": False,
            "message": message,
            "error_code": error_code,
            "data": data,
        },
        status=status_code,
    )