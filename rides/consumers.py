import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Ride, Location


class RideConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.ride_id = self.scope["url_route"]["kwargs"]["ride_id"]

        self.room_group_name = f"ride_{self.ride_id}"

        # Check that ride exists
        ride_exists = await self.check_ride_exists()

        if not ride_exists:
            await self.close()
            return

        # Add WebSocket connection to ride group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send connection confirmation
        await self.send(
            text_data=json.dumps({
                "type": "connection",
                "message": "Ride WebSocket connected",
                "ride_id": self.ride_id
            })
        )

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected: ride={self.ride_id}, code={close_code}")

        if hasattr(self, "room_group_name"):

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):

        try:

            # Make sure data exists
            if not text_data:
                await self.send(
                    text_data=json.dumps({
                        "type": "error",
                        "message": "No data received"
                    })
                )
                return

            # Convert JSON string to Python dictionary
            data = json.loads(text_data)

            # Check latitude and longitude
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

            # Update driver location in database
            location = await self.update_driver_location(
                latitude,
                longitude
            )

            # Send updated location to every client
            # connected to this ride
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
                        "availability_status": location.availability_status,
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

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": str(e)
                })
            )

    @database_sync_to_async
    def check_ride_exists(self):

        return Ride.objects.filter(
            id=self.ride_id
        ).exists()

    @database_sync_to_async
    def update_driver_location(self, latitude, longitude):

        # Get the ride
        ride = Ride.objects.select_related(
            "driver"
        ).get(
            id=self.ride_id
        )

        # Get driver profile
        driver_profile = ride.driver.driver_profile

        # Create or update driver's location
        location, created = Location.objects.get_or_create(
            driver=driver_profile,
            defaults={
                "address": "",
                "latitude": latitude,
                "longitude": longitude,
                "is_available": True,
                "availability_status": "AVAILABLE",
            }
        )

        # If location already exists, update it
        if not created:

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
                    "last_updated",
                ]
            )

        return location

    async def driver_location_update(self, event):

        # Send location update to WebSocket client
        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )