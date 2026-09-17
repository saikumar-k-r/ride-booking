# Production Deployment Checklist

## Environment
- Development, testing and production configurations separated.
- Environment variables used for configuration.
- `.env` excluded from Git.

## Database
- PostgreSQL configured.
- Django connected to PostgreSQL.
- Production migrations executed.
- Database backup and restore verified.

## Redis
- Redis container/service configured.
- Django cache connected to Redis.
- Celery broker configured with Redis.

## Django
- DEBUG disabled in production.
- ALLOWED_HOSTS configured.
- SECRET_KEY loaded from environment.
- CORS/CSRF configured.
- Production security headers enabled.

## Gunicorn
- Django served through Gunicorn.
- Development server is not used for production.
- Gunicorn binds to the application port.

## Celery
- Celery worker configured.
- Redis used as broker.
- Background task processing verified.

## Nginx
- Nginx configured as reverse proxy.
- Requests forwarded to Gunicorn.
- Static/media handling configured.
- Security headers configured.

## Static Files
- STATIC_ROOT configured.
- collectstatic executed.
- Static files verified.

## Media
- MEDIA_ROOT configured.
- Media directory configured.

## Environment Variables
- DJANGO_SECRET_KEY
- DATABASE_URL / database settings
- REDIS_URL
- JWT configuration
- Celery configuration
- Email configuration
- Storage configuration

## Migrations
- `python manage.py makemigrations`
- `python manage.py migrate`
- Migration status verified.

## Security
- DEBUG=False.
- Secrets are not committed.
- JWT authentication enabled.
- Permissions and throttling configured.
- HTTPS/security headers considered for production.

## Logging
- Django application logs enabled.
- Nginx logs available.
- Gunicorn logs available.
- Celery logs available.
- PostgreSQL logs available.

## Monitoring
- Application health endpoint checked.
- Database health checked.
- Redis health checked.
- Container/service status checked.

## Backup
- PostgreSQL backup created using pg_dump.
- Backup restored into a test database.
- Restored database schema verified.

## Rollback
- Version v1 tagged.
- Version v2 tagged.
- Rollback performed using the previous image/version.
- Application health verified after rollback.

## Deployment Flow

Git Push
    ↓
CI Tests
    ↓
Lint
    ↓
Docker Build
    ↓
Container Registry
    ↓
Deployment
    ↓
Nginx
    ↓
Gunicorn
    ↓
Django
    ↓
PostgreSQL / Redis

## Health Verification

- Django application responds successfully.
- PostgreSQL connection verified.
- Redis connection verified.
- Celery worker running.
- Nginx responding.
- Authentication API tested.
- Business API tested.