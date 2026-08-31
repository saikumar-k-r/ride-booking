# Ride Booking Backend Architecture

## Technology Stack
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Django Channels / WebSockets
- Background Workers
- JWT Authentication

## Architecture

Mobile App
    |
REST API / WebSocket
    |
Django / DRF
    |
Business Logic / Services
    |
PostgreSQL + Redis
    |
Background Workers

## Performance
- Advanced Django ORM implemented
- N+1 queries identified and optimized
- Database indexes implemented
- Redis caching implemented
- Cache invalidation implemented
- Nearby-driver search optimized
- API performance benchmark completed

## Real-Time Features
- WebSocket communication
- Real-time ride status
- Real-time driver location
- Notifications
- Background processing
- Retry mechanism

## Security
- JWT authentication
- Permission checks
- Unauthorized-access testing
- Invalid JWT testing
- Object-level access testing
- Invalid payload testing
- WebSocket security testing
- Excessive-request testing

## Testing
Automated tests cover:
- Authentication
- Profiles
- Drivers
- Vehicles
- Rides
- Fare
- Location
- Notifications
- WebSockets
- Permissions

## Final Review
Architecture, database queries, API responses, error handling,
security, logging, tests, documentation and Git history were reviewed.
# Ride Booking Backend Architecture Review

## Jira Story
Django Backend Architecture & Service Layer Refactoring

---

# Task 1 — Review Existing Project

## 1. Objective

Review the complete Django backend and identify architecture, maintainability, code-quality, security, and separation-of-responsibility issues before refactoring.

The project contains:

- Django REST Framework APIs
- PostgreSQL database
- Redis caching
- Celery background tasks
- Django Channels WebSockets
- JWT authentication
- Driver management
- Vehicle management
- Ride management
- Fare calculation
- Driver location tracking
- Nearby driver search
- Notifications

---

# 2. Current Project Structure

```text
ride-booking-main/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
│
├── rides/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py
│   ├── consumers.py
│   ├── routing.py
│   │
│   ├── services/
│   │   ├── fare_service.py
│   │   ├── ride_service.py
│   │   ├── driver_service.py
│   │   ├── location_service.py
│   │   ├── ride_queries.py
│   │   ├── advanced_queries.py
│   │   └── orm_examples.py
│   │
│   ├── migrations/
│   └── tests.py
│
├── notifications/
│   ├── models.py
│   ├── views.py
│   ├── tasks.py
│   └── tests.py
│
├── manage.py
├── requirements.txt
└── ARCHITECTURE.md
Permissions Review
Current permission classes:
IsAdminUserRole
IsDriverUser
IsNormalUser
Findings
Good
Authentication is checked.
Admin access uses Django staff/superuser status.
Driver access is associated with DriverProfile.
Permission logic is separated from views.
Improvement Required
Permission rules should remain focused on authorization only.
Business rules such as:
Driver must be active
Driver must be verified
Ride must belong to user
should be handled through appropriate services or object-level permission checks rather than being duplicated throughout views.
Status
Partially satisfactory.
4. Celery Tasks Review
Celery tasks are located in:
notifications/tasks.py
Current functionality includes:
Reminder notification task
Notification creation task
Retry test task
Good
Celery is configured.
Redis is used as broker/result backend.
Retry functionality is implemented.
Tasks are separated from API views.
Problems Found
1. Notification creation contains database/business logic directly inside the task.
This should eventually call:
notification_service.py
2. print() is used for task logging.
Production code should use structured Django/Python logging.
3. event_id handling needs consistent validation.
The notification service should own duplicate-notification business rules.
Status
Needs service-layer refactoring.
5. WebSocket Consumer Review
WebSocket implementation is located in:
rides/consumers.py
The consumer currently handles:
JWT authentication
Ride authorization
Ride status messages
Driver location updates
Database queries
Database updates
WebSocket broadcasting
Problems Found
High Priority
The consumer contains business logic and direct database operations.
For example:
Ride.objects.select_related(...)
Location.objects.filter(...)
Location.objects.create(...)
ride.status = ...
ride.save(...)
These responsibilities should move into services.
2. Ride status rules are inside the consumer.
The allowed statuses should be centralized in:
ride_service.py
3. Location update logic is inside the consumer.
This should be moved to:
location_service.py
4. Status values are inconsistent.
The model uses:
ONLINE
OFFLINE
BUSY
but the consumer uses:
AVAILABLE
This must be standardized.
5. Broad exception handling
The consumer uses:
except Exception as e:
This can hide programming errors.
Specific exceptions should be handled where possible.
6. JWT authentication logic is embedded in the consumer.
Authentication should eventually be separated into reusable authentication/service functionality where appropriate.
Status
Requires significant refactoring.
6. Models Review
Main models include:
VehicleType
DriverProfile
Vehicle
Location
RideStatus
Ride
Notification
Good
UUID primary keys are used.
Foreign-key relationships are defined.
Appropriate on_delete behavior is mostly used.
Database indexes exist.
Timestamp fields are present.
Notification duplicate protection uses event_id.
Problems Found
1. DriverProfile string method
The model currently contains:
def _str_(self):
instead of:
def __str__(self):
This should be corrected.
2. Location driver allows NULL
Location.driver is nullable, while some business logic assumes a driver exists.
This relationship needs a clear business rule.
3. Availability values are inconsistent
The model defines:
ONLINE
OFFLINE
BUSY
but other code uses:
AVAILABLE
These values must be standardized.
4. Ride status transitions are not centralized.
Different views and consumers implement ride-status changes independently.
A single service should own status transitions.
Status
Good database foundation, but business rules need separation.
7. Serializers Review
Current serializers include:
DriverSerializer
VehicleSerializer
RideSerializer
DriverLocationSerializer
NotificationSerializer
Good
DRF ModelSerializers are used.
Field validation exists.
Read-only fields are defined.
Driver and vehicle validation is implemented.
Problems Found
1. DriverSerializer performs database queries
The serializer contains:
Vehicle.objects.filter(driver=obj).first()
inside get_vehicle().
This can cause repeated database queries when serializing multiple drivers.
The query should be optimized using:
select_related()
or:
prefetch_related()
where appropriate.
2. Business validation is mixed into serializers.
Simple field validation is appropriate in serializers, but complex business rules should move to services.
3. RideSerializer exposes all model fields
It currently uses:
fields = "__all__"
This should be reviewed before production use.
Status
Needs optimization and responsibility cleanup.
8. Views Review
rides/views.py contains a large amount of functionality.
Current views handle:
Drivers
Vehicles
Rides
Ride status
Ride acceptance
Ride cancellation
Fare calculation
Registration
Ride arrival
Ride completion
Ride start
Ride history
Ride aggregation
Driver location
Nearby drivers
Notifications
Advanced ORM examples
Cache handling
Major Problems
1. Business logic exists inside views.
Examples:
Ride status transitions
Ride cancellation
Ride completion
Ride arrival
Driver location updates
Registration
Cache handling
Ride aggregation
These should call services.
2. Database operations exist directly in views.
Examples include:
Ride.objects.get(...)
RideStatus.objects.get(...)
Location.objects.filter(...)
Location.objects.create(...)
Notification.objects.filter(...)
3. Status transition rules are duplicated.
Ride status logic exists in multiple places.
4. Response structures are inconsistent.
Some APIs return:
{
    "success": true,
    "data": {}
}
while others return:
{
    "detail": "Ride not found."
}
or:
{
    "error": "..."
}
A standard response structure is required.
5. Multiple API styles are used.
The project currently mixes:
APIView
GenericAPIView
function-based views
ViewSet
This is not necessarily wrong, but the API design should be standardized where practical.
6. Cache management exists directly in views.
Cache invalidation should be handled by an appropriate service.
7. Advanced ORM demonstration APIs are mixed with production APIs.
These should be separated or restricted to development/testing.
Status
High-priority refactoring required.
9. URLs Review
Current API structure is approximately:
/api/
    token/
    token/refresh/
    register/
    drivers/
    vehicles/
    rides/
    notifications/
Problems Found
1. API versioning is missing.
Target:
/api/v1/
2. Authentication and business APIs are mixed together.
Target:
/api/v1/auth/
/api/v1/users/
/api/v1/drivers/
/api/v1/vehicles/
/api/v1/rides/
/api/v1/notifications/
3. Ride operations are spread across many URL patterns.
Examples:
rides/<id>/status/
rides/<id>/accept/
rides/<id>/cancel/
rides/<id>/fare/
rides/<id>/start/
rides/<id>/arrive/
rides/<id>/complete/
These should be reviewed and consistently organized.
4. Development/ORM endpoints are exposed through normal API URLs.
Examples:
advanced-querysets/
slow-rides/
optimized-rides/
These should not necessarily be production endpoints.
Status
Requires URL restructuring.
10. Services Review
Current service files include:
fare_service.py
location_service.py
ride_service.py
driver_service.py
ride_queries.py
advanced_queries.py
orm_examples.py
Good
Service-layer work has already started.
Examples:
fare_service.py
ride_service.py
location_service.py
ride_queries.py
Problems
1. driver_service.py is empty.
Driver business operations need to be moved here where appropriate.
2. Service responsibilities are not fully standardized.
Some files contain business logic while others contain query-only functions.
3. Duplicate functionality exists.
Ride querying and advanced ORM examples overlap with production query functionality.
4. Service function signatures are inconsistent.
Some views call query functions with arguments that do not match their current definitions.
This must be corrected before final refactoring.
Target
services/
├── user_service.py
├── driver_service.py
├── ride_service.py
├── fare_service.py
└── notification_service.py
Query functions can remain separated where useful, but business operations should have clear ownership.
11. Utilities Review
A dedicated utility structure is not currently established.
Target
utils/
├── validators.py
├── exceptions.py
├── helpers.py
└── constants.py
Candidates
validators.py
Reusable validation such as:
Coordinate validation
Numeric validation
Common input validation
exceptions.py
Application-specific exceptions such as:
RideNotFound
InvalidRideStatus
DriverNotAvailable
DriverNotFound
constants.py
Shared values such as:
Ride statuses
Notification types
Availability statuses
helpers.py
Small reusable helper functions that do not belong to a business service.
Status
Pending.
12. API Response Review
Current APIs use different response structures.
Examples include:
{
    "detail": "Ride not found."
}
{
    "error": "Invalid ride status."
}
{
    "success": true,
    "data": {}
}
Target Success Response
{
    "success": true,
    "message": "Ride created successfully",
    "data": {}
}
Target Error Response
{
    "success": false,
    "message": "Ride cannot be cancelled",
    "error_code": "INVALID_RIDE_STATUS",
    "data": null
}
Status
Pending.
13. Configuration Review
Good
The project contains:
PostgreSQL
Redis
Celery
Django Channels
JWT
DRF
Problems
1. Hardcoded secrets
Sensitive values are directly stored in settings.
These should be moved to environment variables.
2. In-memory WebSocket channel layer
Current configuration uses:
InMemoryChannelLayer
Redis should be used for production/multi-process WebSocket communication.
3. DEBUG enabled
Development configuration currently uses:
DEBUG = True
Production configuration should disable debug mode.
4. ALLOWED_HOSTS is empty
Production deployment requires explicit allowed hosts.
14. Database Query Review
The project already uses:
filter()
exclude()
get()
exists()
count()
values()
values_list()
annotate()
aggregate()
Q()
F()
select_related()
select_for_update()
Good
The project demonstrates knowledge of Django ORM optimization and transactions.
Problems
1. Some query examples are not production functionality.
They should be separated from actual application services.
2. Nearby-driver search loops through database records in Python.
This may become inefficient as driver/location data grows.
3. Serializer queries may cause N+1 query problems.
This needs optimization.
4. Duplicate aggregation/query functions exist.
These should be consolidated.
15. Notification Review
Notification functionality is present in:
notifications/
rides/views.py
notifications/tasks.py
Problems
Notification business operations are distributed across multiple locations.
Target:
API
 ↓
notification_service.py
 ↓
Notification ORM
 ↓
Celery task when required
The service should own:
Creating notifications
Duplicate event handling
Marking notifications read
Marking all notifications read
16. Main Architectural Problems
The most important problems identified are:
Business logic is tightly coupled to views.
WebSocket consumer contains business and database logic.
Ride status transitions are duplicated.
Location update logic is duplicated.
Notification logic is distributed.
API response formats are inconsistent.
API versioning is missing.
Service layer is incomplete.
Utility layer is missing.
Duplicate query functionality exists.
Serializer performs database queries.
Some service function signatures are inconsistent with their callers.
WebSocket availability status is inconsistent with model choices.
Cache logic is mixed with view logic.
Production-sensitive configuration is hardcoded.
In-memory Channels backend is not suitable for multi-process production use.
Advanced ORM/demo endpoints are mixed with production APIs.
17. Refactoring Priority
Priority 1 — Critical
Separate business logic from views.
Centralize ride-status transitions.
Move WebSocket business logic into services.
Fix service/query function inconsistencies.
Standardize location availability values.
Protect sensitive configuration.
Priority 2 — High
Create service modules.
Create notification service.
Create driver service.
Create reusable exceptions and validators.
Standardize API responses.
Introduce API versioning.
Priority 3 — Medium
Optimize serializer queries.
Remove duplicate queries.
Improve logging.
Review advanced ORM endpoints.
Run formatter and linter.
18. Target Architecture
                    Client
                      │
              ┌───────┴────────┐
              │                │
          REST API         WebSocket
              │                │
          Serializer        Consumer
              │                │
              └───────┬────────┘
                      │
                      ▼
                     View
                      │
                      ▼
               Service Layer
                      │
          ┌───────────┴───────────┐
          │                       │
       Queries                 Utilities
          │                       │
          └───────────┬───────────┘
                      │
                     ORM
                      │
                      ▼
                  PostgreSQL

Service Layer
      │
      ├── Celery
      │      ↓
      │    Redis
      │
      └── Channels
             ↓
           Redis
19. Task 1 Conclusion
The project already has a strong foundation with Django REST Framework, PostgreSQL, Redis, Celery, JWT, Channels, permissions, serializers, database indexes, and an initial service layer.
However, business logic is still distributed across views, consumers, serializers, and tasks.
The main refactoring objective is therefore to establish clear separation:
Serializer
    ↓
View
    ↓
Service
    ↓
Query / ORM
    ↓
Database
and:
WebSocket Consumer
    ↓
Service
    ↓
Query / ORM
    ↓
Database
Task 1 review is complete.
Next step:
Task 2 — Identify Responsibilities for Every Major API.

### After you paste it

Save **`ARCHITECTURE.md`**.

Then **don't modify any Python code yet**.

Send me **“Task 1 completed”**, and I'll give you **Task 2**, including the exact responsibility mapping for each of your APIs.