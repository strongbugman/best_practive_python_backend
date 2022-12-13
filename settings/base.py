import os
import logging

from oxalis.amqp import Exchange, Queue

DEBUG = False
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PROJECT_NAME = os.getenv("PROJECT_NAME", "app")

DATABASE = dict(
    url=f"mysql://root:letmein@{os.getenv('MYSQL_HOST', 'mysql')}:3306/{PROJECT_NAME}",
    maxsize=5,
    charset="utf8mb4",
    use_unicode=True,
    connect_timeout=60,
)
READ_DATABASE = dict(
    url=f"mysql://root:letmein@{os.getenv('MYSQL_HOST', 'mysql')}:3306/{PROJECT_NAME}",
    maxsize=6,
    charset="utf8mb4",
    use_unicode=True,
    connect_timeout=60,
)
REDIS = dict(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    max_connections=5,
    socket_timeout=5,
    socket_connect_timeout=5,
)
JWT = {
    "secret": "SECRET KEY!!!",
}
APIMAN = {
    "title": f"{PROJECT_NAME} OpenApi Document",
    "template": "./app/api/base_openapi.yaml",
}
OXALIS = {
    "default_queue": Queue(f"{PROJECT_NAME}.default"),
    "default_exchange": Exchange(f"{PROJECT_NAME}.default"),
    "default_routing_key": "default",
    "timeout": 5,
    "worker_num": 8,
}
OXALIS_CONNECTION_URL = os.environ.get(
    "CELERY_BROKER_URL", "amqp://root:letmein@rabbitmq:5672/"
)
OXALIS_POOL = {"limit": 1000, "timeout": 10 * 60}
SENTRY = {
    "dsn": "",
    "max_breadcrumbs": 20,
    "sample_rate": 1,
    "environment": ENVIRONMENT,
}
APM = {
    "SERVICE_NAME": PROJECT_NAME,
    "ENVIRONMENT": ENVIRONMENT,
    "SERVER_URL": "",
    "SECRET_TOKEN": "",
    "TRANSACTION_SAMPLE_RATE": 1.0,
    "SANITIZE_FIELD_NAMES": ("*jwttoken*",),
}

logging.basicConfig(level=logging.INFO)
