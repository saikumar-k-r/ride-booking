import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

from .models import Ride, Location


User = get_user_model()


class RideConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.ride_id = str(
            self.scope["url_route"]["kwargs"]["ride_id"]
        )

        self.room_group_name = f"ride_{self.ride_id}"

        # -------------------------
        # JWT AUTHENTICATION
        # -------------------------

        query_string = self.scope["query_string"].decode()

        params = parse_qs(query_string)

        token_list = params.get("token")

        if not token_list:
            await self.close(code=4001)
            return

        token = token_list[0]

        try:
            UntypedToken(token)

            user = await self.get_user_from_token(token)

            if user is None:
                await self.close(code=4001)
                return

            self.user = user

        except (InvalidToken, TokenError):
            await self.close(code=4001)
            return

        # -------------------------
        # RIDE AUTHORIZATION
        # -------------------------

        authorized = await self.check_ride_authorization()

        if not authorized:
            await self.close(code=4003)
            return

        # -------------------------
        # CONNECT
        # -------------------------

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(
            text_data=json.dumps({
                "type": "connection",
                "message": "Ride WebSocket connected",
                "ride_id": self.ride_id
            })
        )

    async def disconnect(self, close_code):

        print(
            f"WebSocket disconnected: "
            f"ride={getattr(self, 'ride_id', None)}, "
            f"code={close_code}"
        )

        if hasattr(self, "room_group_name"):

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(
        self,
        text_data=None,
        bytes_data=None
    ):

        try:

            if not text_data:

                await self.send(
                    text_data=json.dumps({
                        "type": "error",
                        "message": "No data received"
                    })
                )

                return

            data = json.loads(text_data)

            # -------------------------
            # RIDE STATUS UPDATE
            # -------------------------

            status = data.get("status")

            if status:

                allowed_statuses = [
                    "REQUESTED",
                    "ACCEPTED",
                    "DRIVER_ARRIVING",
                    "STARTED",
                    "COMPLETED"
                ]

                if status not in allowed_statuses:

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": "Invalid ride status"
                        })
                    )

                    return

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "ride_status_update",
                        "data": {
                            "type": "ride_status",
                            "ride_id": self.ride_id,
                            "status": status
                        }
                    }
                )

                return

            # -------------------------
            # DRIVER LOCATION
            # -------------------------

            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if latitude is None or longitude is None:

                await self.send(
                    text_data=json.dumps({
                        "type": "error",
                        "message": "latitude and longitude are required"
                    })
                )

                return

            location = await self.update_driver_location(
                latitude,
                longitude
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "driver_location_update",
                    "data": {
                        "type": "driver_location",
                        "ride_id": self.ride_id,
                        "latitude": float(location.latitude),
                        "longitude": float(location.longitude),
                        "is_available": location.is_available,
                        "availability_status":
                            location.availability_status
                    }
                }
            )

        except json.JSONDecodeError:

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            )

        except Exception as e:

            print(f"WebSocket error: {e}")

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": str(e)
                })
            )

    # =====================================================
    # JWT USER
    # =====================================================

    @database_sync_to_async
    def get_user_from_token(self, token):

        from rest_framework_simplejwt.backends import TokenBackend
        from django.conf import settings

        try:

            decoded = TokenBackend(
                algorithm="HS256",
                signing_key=settings.SECRET_KEY
            ).decode(
                token,
                verify=True
            )

            user_id = decoded.get("user_id")

            if not user_id:
                return None

            return User.objects.filter(
                id=user_id,
                is_active=True
            ).first()

        except Exception:
            return None

    # =====================================================
    # RIDE AUTHORIZATION
    # =====================================================

    @database_sync_to_async
    def check_ride_authorization(self):

        try:

            ride = Ride.objects.select_related(
                "driver"
            ).get(
                id=self.ride_id
            )

            # Driver authorization
            if ride.driver:

                driver_profile = ride.driver

                if hasattr(driver_profile, "user_id"):

                    if driver_profile.user_id == self.user.id:
                        return True

            # Passenger authorization
            if hasattr(ride, "passenger_id"):

                if ride.passenger_id == self.user.id:
                    return True

            # If your Ride model uses `user` instead
            if hasattr(ride, "user_id"):

                if ride.user_id == self.user.id:
                    return True

            return False

        except Ride.DoesNotExist:

            return False

    # =====================================================
    # RIDE EXISTS
    # =====================================================

    @database_sync_to_async
    def check_ride_exists(self):

        return Ride.objects.filter(
            id=self.ride_id
        ).exists()

    # =====================================================
    # DRIVER LOCATION
    # =====================================================

    @database_sync_to_async
    def update_driver_location(
        self,
        latitude,
        longitude
    ):

        ride = Ride.objects.select_related(
            "driver"
        ).get(
            id=self.ride_id
        )

        driver_profile = ride.driver

        location = Location.objects.filter(
            driver=driver_profile
        ).first()

        if location is None:

            location = Location.objects.create(
                driver=driver_profile,
                address="",
                latitude=latitude,
                longitude=longitude,
                is_available=True,
                availability_status="AVAILABLE"
            )

        else:

            location.latitude = latitude
            location.longitude = longitude
            location.is_available = True
            location.availability_status = "AVAILABLE"

            location.save(
                update_fields=[
                    "latitude",
                    "longitude",
                    "is_available",
                    "availability_status",
                    "last_updated"
                ]
            )

        return location

    # =====================================================
    # RECEIVE LOCATION BROADCAST
    # =====================================================

    async def driver_location_update(self, event):

        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )

    # =====================================================
    # RECEIVE RIDE STATUS BROADCAST
    # =====================================================

    async def ride_status_update(self, event):

        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )