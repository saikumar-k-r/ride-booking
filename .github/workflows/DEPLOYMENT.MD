# CI/CD Deployment & Rollback

## Deployment Flow

Developer
↓
Git Push
↓
GitHub Actions
↓
Install Dependencies
↓
Lint
↓
Django Checks
↓
Migrations
↓
40 Automated Tests
↓
Docker Build
↓
Push Image to GHCR
↓
Production Deployment

## Docker Image

Images are published to GitHub Container Registry (GHCR).

Tags:
- latest
- Git commit SHA

## Production Deployment

Production server pulls the required image:

docker pull ghcr.io/OWNER/REPOSITORY:latest

Then restart the application:

docker compose up -d

Verify:

docker compose ps
docker compose logs web
docker compose logs nginx

## Rollback

Every image is tagged with the Git commit SHA.

Example:

docker pull ghcr.io/OWNER/REPOSITORY:PREVIOUS_SHA

Update the production compose configuration to use the previous SHA and restart:

docker compose up -d

Verify:

docker compose ps
docker compose logs web

## Rollback Strategy

If a new deployment fails:

1. Identify the previous successful Git SHA.
2. Pull the previous Docker image.
3. Update the deployment image tag.
4. Restart the services.
5. Check Django/Nginx logs.
6. Verify API health.