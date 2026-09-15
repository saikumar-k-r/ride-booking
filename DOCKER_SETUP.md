# Docker Setup – Django Mobile Backend

## 1. Overview

This project is containerized using Docker and Docker Compose.

### Architecture

Mobile App
↓
Nginx
↓
Django / Gunicorn
↓
PostgreSQL

Redis
↓
Celery Worker

## 2. Services

The Docker Compose environment contains the following services:

- Web – Django application running with Gunicorn
- PostgreSQL – Application database
- Redis – Cache and Celery message broker
- Celery – Background task worker
- Nginx – Reverse proxy for the Django application

## 3. Prerequisites

Install the following:

- Docker Desktop
- Git
- Python (for local development)

Verify Docker installation:

    docker --version
    docker compose version

## 4. Environment Variables

Create a `.env` file in the project root.

Example:

    DEBUG=False

    POSTGRES_DB=ride_booking
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=your_password
    POSTGRES_HOST=postgres
    POSTGRES_PORT=5432

    REDIS_HOST=redis
    REDIS_PORT=6379

Do not commit the `.env` file to Git.

## 5. Build Docker Images

Build the Django and Celery images:

    docker compose build

For a clean rebuild:

    docker compose build --no-cache

## 6. Start the Application

Start all services in detached mode:

    docker compose up -d

Check running containers:

    docker compose ps

Expected services:

- ride_web
- ride_postgres
- ride_redis
- ride_celery
- ride_nginx

## 7. Stop the Application

Stop all containers:

    docker compose down

To stop and remove volumes:

    docker compose down -v

Note: Removing volumes deletes persistent PostgreSQL data.

## 8. View Logs

View logs for all services:

    docker compose logs

View Django/Web logs:

    docker compose logs web

View Celery logs:

    docker compose logs celery

View PostgreSQL logs:

    docker compose logs postgres

View Redis logs:

    docker compose logs redis

View Nginx logs:

    docker compose logs nginx

Follow logs in real time:

    docker compose logs -f

## 9. PostgreSQL Persistence

PostgreSQL uses a Docker volume to persist database data.

The database data remains available even when containers are restarted.

Restart the environment:

    docker compose down
    docker compose up -d

Verify PostgreSQL:

    docker compose ps

The PostgreSQL container should show:

    healthy

## 10. Redis Configuration

Redis is used for caching and Celery communication.

Django connects to Redis using the Docker service name:

    redis:6379

Celery also uses Redis as the message broker.

Verify Redis:

    docker compose exec redis redis-cli ping

Expected result:

    PONG

## 11. Celery Worker

Celery runs as a separate Docker container.

Check Celery:

    docker compose ps

View Celery logs:

    docker compose logs celery

The Celery worker should remain running without errors.

## 12. Nginx

Nginx works as the reverse proxy in front of Django.

Request flow:

    Client
      ↓
    Nginx
      ↓
    Django / Gunicorn

Nginx forwards incoming API requests to the Django web container.

## 13. API Testing

After starting the environment:

    docker compose up -d

Check services:

    docker compose ps

Test the API through Nginx using a browser or Postman.

Example:

    http://localhost/

API endpoints can be tested through the Nginx exposed port.

## 14. Troubleshooting

### Check container status

    docker compose ps

### Check web logs

    docker compose logs web --tail=50

### Check Celery logs

    docker compose logs celery --tail=50

### Rebuild after changing requirements.txt

    docker compose down
    docker compose build --no-cache
    docker compose up -d

### Check running containers

    docker ps

### Check Docker images

    docker images

## 15. Complete Restart

For a normal restart:

    docker compose down
    docker compose up -d

For a complete rebuild:

    docker compose down
    docker compose build --no-cache
    docker compose up -d

## 16. Verification Checklist

The Dockerized backend is considered ready when:

- [x] Django Docker image builds successfully
- [x] PostgreSQL container works
- [x] Redis container works
- [x] Celery worker works
- [x] Nginx works
- [x] Docker Compose starts the complete backend
- [x] PostgreSQL data persistence is configured
- [x] Docker documentation completed

## 17. Git Commands

Check changes:

    git status

Add the Docker documentation:

    git add DOCKER_SETUP.md

Commit:

    git commit -m "Add Docker setup documentation"

Push to GitHub:

    git push origin main

## 18. Final Status

Dockerization of the Django mobile backend has been completed using Docker Compose.

The environment contains:

- Django / Gunicorn
- PostgreSQL
- Redis
- Celery
- Nginx

All services are configured to work together as a production-style backend environment.