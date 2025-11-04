from datetime import datetime
from app.tasks.celery_app import celery_app
import os

# Resolve log file path relative to the repository, so it works in Docker and locally
LOG_FILE_PATH = os.path.normpath(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "logs", "config_updates.log")
    )
)

def _ensure_logs_dir():
    dirpath = os.path.dirname(LOG_FILE_PATH)
    try:
        os.makedirs(dirpath, exist_ok=True)
    except Exception as e:
        # Print to stdout so worker logs capture it
        print(f"[logger] failed to create logs dir {dirpath}: {e}")

def _write_log_line(line: str):
    _ensure_logs_dir()
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(f"[logger] wrote log line to {LOG_FILE_PATH}")
    except Exception as e:
        # Surface any file write errors to worker logs
        print(f"[logger] failed to write log line: {e}")

# ---- Synchronous helpers (callable from API as fallback) ----
def log_config_update_sync(service_name: str, user_email: str):
    print(f"[logger.sync.log_config_update] start: service={service_name}, user={user_email}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] User '{user_email}' updated config for service '{service_name}'\n"
    _write_log_line(log_line)
    print(f"[logger.sync.log_config_update] done: service={service_name}, user={user_email}")


def log_config_retrieval_sync(service_name: str, user_email: str):
    print(f"[logger.sync.log_config_retrieval] start: service={service_name}, user={user_email}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] User '{user_email}' retrieved config for service '{service_name}'\n"
    _write_log_line(log_line)
    print(f"[logger.sync.log_config_retrieval] done: service={service_name}, user={user_email}")


def log_config_delete_sync(service_name: str, user_email: str):
    print(f"[logger.sync.log_config_delete] start: service={service_name}, user={user_email}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] User '{user_email}' deleted config for service '{service_name}'\n"
    _write_log_line(log_line)
    print(f"[logger.sync.log_config_delete] done: service={service_name}, user={user_email}")


def log_config_version_compare_sync(service_name: str, user_email: str, version1: int, version2: int):
    print(f"[logger.sync.log_config_version_compare] start: service={service_name}, user={user_email}, v1={version1}, v2={version2}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] User '{user_email}' compared versions {version1} and {version2} for service '{service_name}'\n"
    _write_log_line(log_line)
    print(f"[logger.sync.log_config_version_compare] done: service={service_name}, user={user_email}, v1={version1}, v2={version2}")


def user_login_log_sync(user_email: str):
    print(f"[logger.sync.user_login_log] start: user={user_email}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] User '{user_email}' logged in\n"
    _write_log_line(log_line)
    print(f"[logger.sync.user_login_log] done: user={user_email}")


def user_logout_log_sync(user_email: str):
    print(f"[logger.sync.user_logout_log] start: user={user_email}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] User '{user_email}' logged out\n"
    _write_log_line(log_line)
    print(f"[logger.sync.user_logout_log] done: user={user_email}")


def user_registration_log_sync(user_email: str, user_role: str):
    print(f"[logger.sync.user_registration_log] start: user={user_email}, role={user_role}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] New user registered with email '{user_email}' with {user_role} privileges\n"
    _write_log_line(log_line)
    print(f"[logger.sync.user_registration_log] done: user={user_email}, role={user_role}")

# ---- Celery tasks delegate to sync helpers ----
@celery_app.task(bind=True)
def ping(self):
    """Simple task to verify the worker is running and can execute tasks."""
    print("[logger.ping] task received")
    return "pong"

@celery_app.task(bind=True)
def log_config_update(self, service_name: str, user_email: str):
    log_config_update_sync(service_name, user_email)

@celery_app.task(bind=True)
def log_config_retrieval(self, service_name: str, user_email: str):
    log_config_retrieval_sync(service_name, user_email)

@celery_app.task(bind=True)
def log_config_delete(self, service_name: str, user_email: str):
    log_config_delete_sync(service_name, user_email)

@celery_app.task(bind=True)
def log_config_version_compare(self, service_name: str, user_email: str, version1: int, version2: int):
    log_config_version_compare_sync(service_name, user_email, version1, version2)

@celery_app.task(bind=True)
def user_login_log(self, user_email: str):
    user_login_log_sync(user_email)

@celery_app.task(bind=True)
def user_logout_log(self, user_email: str):
    user_logout_log_sync(user_email)

@celery_app.task(bind=True)
def user_registration_log(self, user_email: str, user_role: str):
    user_registration_log_sync(user_email, user_role)
