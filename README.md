# ⚙️ ConfigSync — Centralized Configuration Management System

**ConfigSync** is a self-hosted **configuration management platform** built with **FastAPI**, designed to centralize and securely manage environment variables and configuration files for multiple microservices.

It eliminates scattered `.env` files, ensures **consistent configuration across environments**, and provides a single API for **storing**, **fetching**, **versioning**, and **synchronizing** configurations — now powered by **asynchronous background logging** using **Celery + Redis**.

---

## 🚀 Features

### ✅ Core Functionality

* **FastAPI backend** with modular architecture
* **PostgreSQL** for persistent configuration storage
* **Alembic** for **database migrations and version control**
* **JWT-based authentication** with **admin role-based access**
* **API key authentication** for external service integrations
* **Celery + Redis** for background logging and async task execution
* **Containerized** with Docker + Docker Compose
* **Persistent volumes** for Postgres data
* **Hot reload** for development

---

## 🧠 Architecture Overview

ConfigSync is built around a **modular microservice-style architecture**:

```
                        ┌────────────────────┐
                        │     FastAPI API    │
                        │  (app/main.py)     │
                        └────────┬───────────┘
                                 │
               ┌────────────────┼────────────────┐
               │                │                │
               ▼                ▼                ▼
        PostgreSQL        Redis Message       Celery Worker
       (Persistent DB)      Broker/Queue     (Async Logging)
```

**Flow Example:**

1. User (or admin) sends a `POST /config/update` request.
2. FastAPI saves the new config in **PostgreSQL**.
3. A **Celery task** is dispatched asynchronously to log this update.
4. The Celery worker (connected to Redis) writes structured logs into
   `app/logs/config_logs.log` with details like:

   * Timestamp
   * User who made the change
   * Service name
   * Change summary
5. The API returns instantly — keeping the app responsive.

---

## 🔄 Example: Celery Task Flow

Here’s how a config update triggers a Celery background task internally:

```python
# app/tasks/celery_worker.py

from celery import Celery
import logging

celery_app = Celery(
    "configsync",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

@celery_app.task
def log_config_update(user_email: str, service_name: str, action: str):
    logger = logging.getLogger("config_logger")
    logger.info(f"User={user_email} | Service={service_name} | Action={action}")
```

And when a user updates a config:

```python
# app/api/routes_config.py

from app.tasks.celery_worker import log_config_update

@router.post("/config/update")
def update_config(...):
    # Save config to DB ...
    log_config_update.delay(user.email, config.name, "Config updated")
    return {"status": "success", "message": "Update scheduled"}
```

---

## 🧩 API Endpoints

| Method | Endpoint                     | Description                                           | Auth Required |
| ------ | ---------------------------- | ----------------------------------------------------- | ------------- |
| `POST` | `/auth/signup`               | Register a new user                                   | ❌             |
| `POST` | `/auth/login`                | Login and get JWT                                     | ❌             |
| `GET`  | `/config/get?service=<name>` | Fetch configuration for a service                     | ✅             |
| `POST` | `/config/update`             | Create or update configuration (triggers Celery task) | ✅             |
| `GET`  | `/`                          | Health check                                          | ❌             |

### 🔐 Role-Based Access Control

| Role    | Permissions                              |
| ------- | ---------------------------------------- |
| `admin` | Full access to all configs and users     |
| `user`  | Can only manage their own configurations |

---

## 🏗️ Tech Stack

| Layer                    | Tool                    |
| ------------------------ | ----------------------- |
| **Language**             | Python 3.11             |
| **Framework**            | FastAPI                 |
| **Database**             | PostgreSQL              |
| **ORM**                  | SQLAlchemy              |
| **Migrations**           | Alembic                 |
| **Auth**                 | JWT & API Key           |
| **Task Queue**           | Celery + Redis          |
| **Containerization**     | Docker + Docker Compose |
| **Monitoring (planned)** | Prometheus + Grafana    |

---

## 🧰 Project Structure

```
ConfigSync/
├── app/
│   ├── api/
│   │   ├── routes_auth.py
│   │   └── routes_config.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── crud.py
│   │   ├── database.py
│   │   └── models.py
│   ├── tasks/
│   │   └── celery_worker.py
│   ├── logs/
│   │   └── config_logs.log
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   └── config_schema.py
│   └── main.py
├── alembic/
│   ├── versions/
│   └── env.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start (Docker Compose)

### 1️⃣ Build and start all services

```bash
docker-compose up --build
```

### 2️⃣ Run in background

```bash
docker-compose up -d
```

### 3️⃣ View Celery task logs

```bash
docker-compose logs -f celery
```

### 4️⃣ Stop containers

```bash
docker-compose down
```

*(PostgreSQL data persists in the named volume `configsync_data`.)*

---

## 🧪 API Testing Examples

### 🔸 Register a New User

```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@email.com", "password": "password123"}'
```

### 🔸 Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@email.com", "password": "password123"}'
```

### 🔸 Update or Create a Config (Triggers Celery Task)

```bash
curl -X POST "http://localhost:8000/config/update" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "name": "payment-service",
    "config": {
      "API_URL": "https://api.example.com",
      "TIMEOUT": 30
    }
  }'
```

### 🔸 Fetch a Config

```bash
curl "http://localhost:8000/config/get?service=payment-service" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## 🔐 Environment Variables

| Variable       | Description                           | Default                                                 |
| -------------- | ------------------------------------- | ------------------------------------------------------- |
| `DATABASE_URL` | PostgreSQL connection URI             | `postgresql://configsync:configsync@db:5432/configsync` |
| `SECRET_KEY`   | JWT signing key                       | `supersecretkey`                                        |
| `API_KEY`      | Service-to-service authentication key | `supersecretkey`                                        |
| `REDIS_URL`    | Redis connection URI                  | `redis://redis:6379/0`                                  |
| `PROJECT_NAME` | Display name for API                  | `ConfigSync`                                            |

---

## 🧵 Volumes and Mounts

| Container | Mount Type     | Host Path / Volume                             |
| --------- | -------------- | ---------------------------------------------- |
| `backend` | Bind Mount     | `./app` → `/app/app`                           |
| `db`      | Named Volume   | `configsync_data` → `/var/lib/postgresql/data` |
| `redis`   | Ephemeral      | Redis in-memory queue                          |
| `celery`  | Shared Network | Communicates with backend + Redis              |

---

## ⚙️ Upcoming Enhancements

| Feature                             | Description                                 |
| ----------------------------------- | ------------------------------------------- |
| 🪣 **Config version history**       | Track who changed what and when             |
| 📊 **Prometheus + Grafana metrics** | Monitor config updates and API activity     |
| 🧪 **Pytest test suite**            | Automated testing for CRUD and Celery tasks |
| ☁️ **Terraform simulation**         | Infrastructure-as-code reproducibility      |

---

## 💡 Why This Project Matters

Modern microservice architectures rely on distributed configurations.
**ConfigSync** provides a lightweight, developer-friendly way to ensure **consistent**, **auditable**, and **asynchronously logged** configuration management — acting as an internal alternative to **AWS Parameter Store** or **HashiCorp Vault Lite**.

---

## 💬 Resume Highlight

> **Built “ConfigSync” — a FastAPI-based configuration management system with JWT authentication, Alembic migrations, Dockerized PostgreSQL persistence, and Celery + Redis for asynchronous background logging of configuration updates.**

---

## 👨‍💻 Author

**Aditya S Joshi**
Backend & Cloud-Native Developer
*“Clean, minimal, and production-minded engineering.”*