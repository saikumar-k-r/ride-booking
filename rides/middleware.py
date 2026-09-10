import jwt
from urllib.parse import parse_qs

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model


@database_sync_to_async
def get_user(token):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = payload.get("user_id")

        if not user_id:
            return None

        User = get_user_model()
        return User.objects.get(id=user_id)

    except Exception:
        return None


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):

        query_string = scope.get("query_string", b"").decode()

        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        if not token:
            await send({
                "type": "websocket.close",
                "code": 4001,
            })
            return

        user = await get_user(token)

        if user is None:
            await send({
                "type": "websocket.close",
                "code": 4003,
            })
            return

        scope["user"] = user

        return await super().__call__(
            scope,
            receive,
            send
        )
import time
import uuid
import logging

logger = logging.getLogger("api")


class RequestTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = self.get_response(request)
            return response
        except Exception:
            logger.exception(
                "API_ERROR request_id=%s method=%s endpoint=%s user_id=%s",
                request_id,
                request.method,
                request.path,
                getattr(request.user, "id", "anonymous"),
            )
            raise
        finally:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000, 2
            )

            logger.info(
                "API_REQUEST request_id=%s method=%s endpoint=%s "
                "user_id=%s status=%s execution_time_ms=%s",
                request_id,
                request.method,
                request.path,
                getattr(request.user, "id", "anonymous"),
                getattr(locals().get("response"), "status_code", 500),
                duration_ms,
            )

            if "response" in locals():
                response["X-Request-ID"] = request_id