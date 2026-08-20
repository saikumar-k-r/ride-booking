# Ride Booking – Database Documentation

## 1. Project Overview

This project implements the database architecture for a Ride Booking mobile application using Django and PostgreSQL.

The database is designed to manage passengers, drivers, vehicles, locations, rides, and ride statuses.

---

## 2. Database Models

The application contains the following business models:

1. VehicleType
2. DriverProfile
3. Vehicle
4. Location
5. RideStatus
6. Ride

The Django built-in User model is used for passenger and driver authentication.

---

## 3. Entity Relationships

```text
User
 ├── DriverProfile
 │      └── Vehicle
 │             └── VehicleType
 │
 └── Ride
        ├── DriverProfile
        ├── Vehicle
        ├── Location (Pickup)
        ├── Location (Drop)
        └── RideStatus

Relationship Details
Relationship
Type
Description
User → DriverProfile
One-to-One
A user can have one driver profile
DriverProfile → Vehicle
One-to-Many
A driver can have multiple vehicles
VehicleType → Vehicle
One-to-Many
One vehicle type can be assigned to multiple vehicles
User → Ride
One-to-Many
A passenger can have multiple rides
DriverProfile → Ride
One-to-Many
A driver can complete multiple rides
Vehicle → Ride
One-to-Many
A vehicle can be used for multiple rides
Location → Ride
One-to-Many
A location can be used by multiple rides
RideStatus → Ride
One-to-Many
A status can be assigned to multiple rides
4. Model Details
VehicleType
Stores vehicle categories such as Sedan, SUV, etc.
Important fields:
UUID primary key
Name
Active status
Created timestamp
Unique vehicle type name
DriverProfile
Stores driver-specific information.
Important fields:
UUID primary key
User relationship
License number
Verification status
Active status
Created timestamp
Updated timestamp
Constraints:
One-to-one relationship with User
License number must be unique
Vehicle
Stores vehicles registered by drivers.
Important fields:
UUID primary key
Driver relationship
Vehicle type relationship
Registration number
Model name
Active status
Created timestamp
Updated timestamp
Constraints:
Registration number must be unique
Driver must exist
Vehicle type must exist
Location
Stores pickup and drop locations.
Important fields:
UUID primary key
Address
Latitude
Longitude
Created timestamp
The latitude and longitude values allow the application to identify the geographical location.
RideStatus
Stores available ride statuses.
Examples:
Requested
Accepted
Started
Completed
Cancelled
Important fields:
UUID primary key
Status code
Status name
Active status
Created timestamp
The status code is unique.
Ride
The Ride model represents a passenger's booking.
Important fields:
UUID primary key
Passenger
Driver
Vehicle
Pickup location
Drop location
Ride status
Fare
Requested timestamp
Completed timestamp
Created timestamp
Updated timestamp
The driver, vehicle, and completed timestamp can be empty when a ride has not yet been assigned or completed.
5. Primary Keys
UUIDs are used as primary keys for the business models.
Benefits:
Globally unique identifiers
Better suited for distributed systems
Avoids predictable sequential IDs
Suitable for mobile and API-based applications
6. Foreign Keys
Foreign keys maintain relationships between tables.
Examples:
DriverProfile → User
Vehicle → DriverProfile
Vehicle → VehicleType
Ride → User
Ride → DriverProfile
Ride → Vehicle
Ride → Location
Ride → RideStatus
7. Database Constraints
The database implements the following constraints:
Unique Constraints
Vehicle type name
Driver license number
Vehicle registration number
Ride status code
NOT NULL Constraints
Required fields are configured so that they cannot contain NULL values.
Examples:
Driver profile user
Vehicle driver
Vehicle type
Vehicle registration number
Ride passenger
Ride pickup location
Ride drop location
Ride status
Foreign Key Constraints
Foreign keys ensure that referenced records exist.
PROTECT
Used for important reference data such as:
VehicleType
Location
RideStatus
This prevents deletion when related records exist.
CASCADE
Used where dependent records should be removed with their parent.
SET_NULL
Used for optional ride relationships such as:
Driver
Vehicle
This allows a ride to remain when a driver or vehicle is removed.
8. Database Indexes
Indexes were added to frequently queried fields.
Examples:
DriverProfile license number
DriverProfile verification and active status
Vehicle driver
Vehicle vehicle type
Vehicle active status
Ride passenger
Ride driver
Ride status
Ride requested timestamp
Location latitude and longitude
Indexes improve query performance for frequently accessed data.
9. Django Admin Configuration
All business models are registered in Django Admin.
The admin interface includes:
List display
Search fields
Filters
Ordering
The Ride Admin provides:
Passenger
Driver
Vehicle
Status
Fare
Requested time
Completed time
Search is available for passenger username, driver username, and vehicle registration number.
10. Migration Testing
Django migrations were tested using:
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations rides
The migration was successfully applied:
[X] 0001_initial
Migration rollback was also tested:
python manage.py migrate rides zero
The migration was successfully rolled back:
[ ] 0001_initial
The migration was then restored:
python manage.py migrate rides
Final verification:
[X] 0001_initial
11. Business Rules
A user can have a driver profile.
A driver can have multiple vehicles.
Every vehicle belongs to a vehicle type.
A passenger can create multiple rides.
A ride can optionally be assigned to a driver.
A ride can optionally be assigned to a vehicle.
Every ride has a pickup and drop location.
Every ride has a valid ride status.
Vehicle registration numbers must be unique.
Driver license numbers must be unique.
Ride status codes must be unique.
Completed time remains empty until the ride is completed.
12. Acceptance Criteria
Requirement
Status
Business database schema completed
✅
Relationships implemented
✅
PostgreSQL tables verified
✅
Database constraints implemented
✅
Django Admin configured
✅
Migrations tested
✅
Migration rollback tested
✅
ER diagram documented
✅
Models documented
✅
Business rules documented
✅
13. Technology Stack
Python
Django
PostgreSQL
Django ORM
Django Admin
UUID
Django Migrations
14. Conclusion
The Ride Booking business database has been successfully designed and implemented using Django and PostgreSQL.
The schema includes appropriate relationships, constraints, indexes, timestamps, UUID primary keys, Django Admin configuration, and migration testing.
The database is ready for further API and business-logic development.
# Database Documentation

## 1. Overview

This document describes the database design, models, relationships,
constraints, indexes, and business rules of the Ride Booking Django project.

The application uses Django ORM with a relational database.

---

## 2. Database Models

The main application models are:

1. User
2. Location
3. RideStatus
4. DriverProfile
5. Ride
6. Fare

Django's built-in `User` model is used for authentication and user accounts.

---

## 3. Entity Relationships

### User
A User can be associated with:
- Passenger rides
- A DriverProfile

### DriverProfile
A DriverProfile belongs to one User.

### Location
A Location can be used as:
- Pickup location
- Drop location

### RideStatus
A Ride has one RideStatus.

### Ride
A Ride belongs to:
- One passenger/User
- One pickup Location
- One drop Location
- One RideStatus
- Optionally one DriverProfile

### Fare
A Fare is associated with a Ride and stores fare calculation information.

---

## 4. Model Details

### User

Uses Django's built-in authentication User model.

Important fields include:
- id
- username
- password
- email

### Location

Stores geographical information for pickup and drop locations.

Typical fields:
- id
- address
- latitude
- longitude

### RideStatus

Stores the status of a ride.

Typical statuses include:
- REQUESTED
- ACCEPTED
- COMPLETED
- CANCELLED

### DriverProfile

Stores driver-specific information.

Important fields include:
- user
- license_number
- is_active

### Ride

Stores ride booking information.

Important fields include:
- passenger
- driver
- pickup_location
- drop_location
- status
- requested_at
- completed_at
- created_at
- updated_at

### Fare

Stores fare calculation information such as:
- base fare
- distance fare
- time fare
- surge
- total

---

## 5. Primary Keys and Foreign Keys

Each model uses a primary key to uniquely identify records.

Foreign-key relationships include:

- DriverProfile → User
- Ride → User (passenger)
- Ride → DriverProfile (driver)
- Ride → Location (pickup)
- Ride → Location (drop)
- Ride → RideStatus
- Fare → Ride

Foreign keys maintain referential integrity between related records.

---

## 6. Database Constraints

The database uses Django model constraints and relational integrity rules.

### Unique Constraints

Driver license numbers should be unique so that one license cannot be
registered for multiple driver profiles.

Ride status codes should uniquely identify each status.

### NOT NULL Constraints

Required fields such as passenger, pickup location, drop location,
and ride status must contain valid values.

### Foreign Key Constraints

Foreign keys ensure that referenced records exist before relationships
can be created.

### Delete Behavior

Relationships use appropriate Django `on_delete` behavior such as:

- `PROTECT` where related records must not be deleted accidentally.
- `CASCADE` where dependent records should be removed with their parent.
- `SET_NULL` where an optional relationship should become NULL.

---

## 7. Indexes

Indexes are used to improve query performance.

Important fields for indexing include:

- Ride status
- Driver
- Passenger
- Created/requested timestamps
- Ride status code

Indexes are particularly useful for finding requested rides and
retrieving rides belonging to a particular passenger or driver.

---

## 8. Admin Configuration

The Django admin interface provides management of database records.

Administrators can manage:

- Users
- Driver profiles
- Locations
- Ride statuses
- Rides
- Fare records

Admin configuration helps with development, testing, and database
administration.

---

## 9. Migration Testing and Rollback

Database schema changes are managed using Django migrations.

Typical commands are:

```bash
python manage.py makemigrations
python manage.py migrate
## 11. Transaction & Concurrency

Ride acceptance uses Django database transactions to prevent two drivers from accepting the same ride at the same time.

The `accept_ride` service uses:

```python
with transaction.atomic():
### 12. Indexing

```markdown
## 12. Indexing

Database indexes are used on fields that are frequently searched or filtered.

Important fields for indexing include:

- Ride status
- Driver
- User
- Ride timestamps
- Foreign key fields

Indexes improve query performance when retrieving rides by status, driver, or related records.

Django automatically creates indexes for foreign key relationships unless otherwise configured.
## 13. Data Integrity

Data integrity is maintained through Django model relationships, database constraints, validation, and controlled ride-status transitions.

Important integrity rules include:

- A ride must have a valid status.
- A ride can be assigned to a valid driver profile.
- A driver must have an active driver profile before accepting a ride.
- A ride must be in `REQUESTED` status before acceptance.
- A ride must be `ACCEPTED` before it can be started.
- Ride updates are saved using database transactions where concurrency could occur.

These rules help prevent invalid or inconsistent ride data.
## 14. Summary

The Ride Booking database is designed around users, driver profiles, rides, ride statuses, locations, and fare information.

The database structure supports the complete ride lifecycle:

`REQUESTED → ACCEPTED → STARTED → ARRIVED → COMPLETED`

Django models and database relationships maintain data consistency, while transactions and row-level locking protect critical operations such as ride acceptance.

The implemented tests and Django system checks confirm that the current database and ride-booking functionality operate without detected errors.