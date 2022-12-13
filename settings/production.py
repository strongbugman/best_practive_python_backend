from .base import *

SENTRY["dsn"] = ""
APIMAN = {
    "title": f"{PROJECT_NAME} OpenApi Document",
    "specification_url": "",
    "swagger_url": "",
    "redoc_url": "",
}
DATABASE["maxsize"] = 10
READ_DATABASE["maxsize"] = 10
REDIS["max_connections"] = 10

SENTRY["sample_rate"] = 0.01
