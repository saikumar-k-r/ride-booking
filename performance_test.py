import time
import requests
import psutil

BASE_URL = "http://127.0.0.1:8000"

# Put your existing Django username/password here
USERNAME = "YOUR_USERNAME"
PASSWORD = "YOUR_PASSWORD"


def get_token():
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/token/",
        json={
            "username": "aaa",
            "password": "aaa1234567890",
        },
    )

    print("Login Status:", response.status_code)

    if response.status_code != 200:
        print("Login failed:", response.text)
        return None

    return response.json()["access"]


def test_api(name, url, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    process = psutil.Process()

    memory_before = process.memory_info().rss / (1024 * 1024)
    cpu_before = process.cpu_percent(interval=None)

    start = time.perf_counter()

    response = requests.get(
        url,
        headers=headers
    )

    end = time.perf_counter()

    cpu_after = process.cpu_percent(interval=0.1)
    memory_after = process.memory_info().rss / (1024 * 1024)

    print("\n" + "=" * 50)
    print(f"API: {name}")
    print(f"URL: {url}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {(end - start) * 1000:.2f} ms")
    print(f"CPU Usage: {cpu_after - cpu_before:.2f}%")
    print(f"Memory Usage: {memory_after:.2f} MB")
    print(f"Memory Change: {memory_after - memory_before:.2f} MB")


if __name__ == "__main__":

    print("\nAPI PERFORMANCE BASELINE")
    print("=" * 50)

    token = get_token()

    if not token:
        print("Cannot run performance test without JWT token.")
        exit()

    test_api(
        "Ride History",
        f"{BASE_URL}/api/v1/rides/",
        token
    )

    test_api(
        "Nearby Drivers",
        f"{BASE_URL}/api/v1/drivers/nearby/?latitude=14.44&longitude=79.99&radius=5",
        token
    )