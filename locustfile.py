from locust import HttpUser, between, task


class RideBookingUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def ride_history(self):
        self.client.get("/api/v1/rides/")