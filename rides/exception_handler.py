from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    message = "Request failed"

    if isinstance(response.data, dict):
        message = response.data.get("detail", message)

    response.data = {
        "success": False,
        "message": str(message),
        "error_code": f"HTTP_{response.status_code}",
    }

    return response