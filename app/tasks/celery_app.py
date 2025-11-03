from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "configsync",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.logger"],
)

celery_app.conf.task_routes = {
    "app.tasks.logger.log_config_update": {"queue": "default"},
    "app.tasks.logger.log_config_retrieval": {"queue": "default"},
    "app.tasks.logger.user_login_log": {"queue": "default"},
    "app.tasks.logger.user_logout_log": {"queue": "default"},
    "app.tasks.logger.user_registration_log": {"queue": "default"}
}

# Ensure the worker consumes the same default queue used by task routes
celery_app.conf.task_default_queue = "default"