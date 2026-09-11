import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from django.contrib.auth import get_user_model

from .models import Ride
from .services.driver_service import update_driver_location


User = get_user_model()


class RideConsumer(AsyncWebsocketConsumer):

    # =====================================================
    # CONNECT
    # =====================================================

    async def connect(self):

        self.ride_id = str(
            self.scope["url_route"]["kwargs"]["ride_id"]
        )

        self.room_group_name = f"ride_{self.ride_id}"

        # -------------------------------------------------
        # JWT AUTHENTICATION
        # -------------------------------------------------

        query_string = self.scope["query_string"].decode()

        params = parse_qs(query_string)

        token_list = params.get("token")

        if not token_list:
            await self.close(code=4001)
            return

        token = token_list[0]

        try:

            user = await self.get_user_from_token(token)

            if user is None:
                await self.close(code=4001)
                return

            self.user = user

        except (InvalidToken, TokenError):
            await self.close(code=4001)
            return

        # -------------------------------------------------
        # RIDE AUTHORIZATION
        # -------------------------------------------------

        authorized = await self.check_ride_authorization()

        if not authorized:
            await self.close(code=4003)
            return

        # -------------------------------------------------
        # JOIN RIDE GROUP
        # -------------------------------------------------

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # -------------------------------------------------
        # CONNECTION RESPONSE
        # -------------------------------------------------

        await self.send(
            text_data=json.dumps({
                "type": "connection",
                "message": "Ride WebSocket connected",
                "ride_id": self.ride_id
            })
        )

    # =====================================================
    # DISCONNECT
    # =====================================================

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

    # =====================================================
    # RECEIVE MESSAGE
    # =====================================================

    async def receive(
        self,
        text_data=None,
        bytes_data=None
    ):

        try:

            # -------------------------------------------------
            # EMPTY MESSAGE
            # -------------------------------------------------

            if not text_data:

                await self.send(
                    text_data=json.dumps({
                        "type": "error",
                        "message": "No data received"
                    })
                )

                return

            # -------------------------------------------------
            # JSON PARSE
            # -------------------------------------------------

            data = json.loads(text_data)

            # =================================================
            # DRIVER LOCATION UPDATE
            # =================================================

            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if latitude is not None or longitude is not None:

                # Only assigned driver can update location
                assigned_driver = await self.is_assigned_driver()

                if not assigned_driver:

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": (
                                "Only the assigned driver "
                                "can update location"
                            )
                        })
                    )

                    return

                if latitude is None or longitude is None:

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": (
                                "latitude and longitude "
                                "are required"
                            )
                        })
                    )

                    return

                # Validate coordinates
                try:

                    latitude = float(latitude)
                    longitude = float(longitude)

                except (TypeError, ValueError):

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": (
                                "latitude and longitude "
                                "must be numbers"
                            )
                        })
                    )

                    return

                if not (-90 <= latitude <= 90):

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": "Invalid latitude"
                        })
                    )

                    return

                if not (-180 <= longitude <= 180):

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": "Invalid longitude"
                        })
                    )

                    return

                driver = await self.get_driver_profile()

                location = await update_driver_location(
                    driver=driver,
                    latitude=latitude,
                    longitude=longitude,
                )

                # Broadcast location to passenger/driver
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
                                location.availability_status,
                        }
                    }
                )

                return

            # =================================================
            # RIDE STATUS UPDATE
            # =================================================

            status = data.get("status")

            if status:

                allowed_statuses = [
                    "REQUESTED",
                    "ACCEPTED",
                    "DRIVER_ARRIVING",
                    "STARTED",
                    "COMPLETED",
                ]

                if status not in allowed_statuses:

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": "Invalid ride status"
                        })
                    )

                    return

                # Only assigned driver can broadcast
                # ride status changes through WebSocket.
                assigned_driver = await self.is_assigned_driver()

                if not assigned_driver:

                    await self.send(
                        text_data=json.dumps({
                            "type": "error",
                            "message": (
                                "Only the assigned driver "
                                "can update ride status"
                            )
                        })
                    )

                    return

                # Broadcast status to everyone
                # connected to this ride.
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "ride_status_update",
                        "data": {
                            "type": "ride_status",
                            "ride_id": self.ride_id,
                            "status": status,
                        }
                    }
                )

                return

            # =================================================
            # INVALID MESSAGE
            # =================================================

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": (
                        "Invalid message. Send either "
                        "latitude/longitude or status."
                    )
                })
            )

        # -------------------------------------------------
        # INVALID JSON
        # -------------------------------------------------

        except json.JSONDecodeError:

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            )

        # -------------------------------------------------
        # GENERAL ERROR
        # -------------------------------------------------

        except Exception as e:

            print(
                f"WebSocket error: "
                f"ride={getattr(self, 'ride_id', None)}, "
                f"error={e}"
            )

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": "WebSocket processing error"
                })
            )

    # =====================================================
    # JWT USER
    # =====================================================

    @database_sync_to_async
    def get_user_from_token(self, token):

        try:

            access_token = AccessToken(token)

            user_id = access_token.get("user_id")

            if not user_id:
                return None

            return User.objects.filter(
                id=user_id,
                is_active=True
            ).first()

        except (InvalidToken, TokenError):

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

            # -------------------------------------------------
            # DRIVER
            # -------------------------------------------------

            if ride.driver:

                driver_profile = ride.driver

                if hasattr(driver_profile, "user_id"):

                    if driver_profile.user_id == self.user.id:
                        return True

            # -------------------------------------------------
            # PASSENGER
            # -------------------------------------------------

            if hasattr(ride, "passenger_id"):

                if ride.passenger_id == self.user.id:
                    return True

            # -------------------------------------------------
            # ALTERNATIVE USER FIELD
            # -------------------------------------------------

            if hasattr(ride, "user_id"):

                if ride.user_id == self.user.id:
                    return True

            return False

        except Ride.DoesNotExist:

            return False

    # =====================================================
    # CHECK ASSIGNED DRIVER
    # =====================================================

    @database_sync_to_async
    def is_assigned_driver(self):

        try:

            ride = Ride.objects.select_related(
                "driver"
            ).get(
                id=self.ride_id
            )

            if not ride.driver:
                return False

            driver_profile = ride.driver

            if not hasattr(driver_profile, "user_id"):
                return False

            return driver_profile.user_id == self.user.id

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
    # DRIVER PROFILE
    # =====================================================

    @database_sync_to_async
    def get_driver_profile(self):

        if not hasattr(self.user, "driver_profile"):

            raise ValueError(
                "User is not a driver."
            )

        return self.user.driver_profile

    # =====================================================
    # DRIVER LOCATION BROADCAST
    # =====================================================

    async def driver_location_update(self, event):

        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )

    # =====================================================
    # RIDE STATUS BROADCAST
    # =====================================================

    async def ride_status_update(self, event):

        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )