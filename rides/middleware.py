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