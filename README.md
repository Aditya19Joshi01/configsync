# ⚙️ ConfigSync — Centralized Configuration Management System

**ConfigSync** is a self-hosted **configuration management platform** built with **FastAPI**, designed to centralize and securely manage environment variables and configuration files across microservices.

It eliminates scattered `.env` files, ensures **consistent configuration across environments**, and provides a single API for **storing**, **fetching**, **versioning**, **comparing**, **deleting**, and **rolling back** configurations — all with **asynchronous background logging** via **Celery + Redis**.

---

## 🚀 Features

### ✅ Core Functionality

* **FastAPI backend** with modular architecture
* **PostgreSQL** + **SQLAlchemy** for persistent storage
* **Alembic** for database migrations
* **JWT-based authentication** with **role-based access (admin/user)**
* **Token revocation** to invalidate active sessions
* **Config versioning and rollback support**
* **Config diffing** between any two saved versions
* **Celery + Redis** for background audit logging
* **Containerized** using Docker + Docker Compose
* **Persistent Postgres volumes** for data durability
* **Hot reload** for development environments

---

## 🧠 Architecture Overview

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

### 🔄 Flow Example

1. User sends a `POST /config/update` request.
2. FastAPI stores the new config and creates a version record in **PostgreSQL**.
3. A **Celery task** logs the update asynchronously.
4. The Celery worker writes structured logs into `app/logs/config_logs.log`.
5. The API instantly responds — keeping the system responsive and reliable.

---

## 🧩 Key API Endpoints

| Method   | Endpoint                                                        | Description                       | Auth |
| -------- | --------------------------------------------------------------- | --------------------------------- | ---- |
| `POST`   | `/auth/register`                                                | Register a new user               | ❌    |
| `POST`   | `/auth/login`                                                   | Login and get JWT                 | ❌    |
| `POST`   | `/auth/logout`                                                  | Revoke token (logout)             | ✅    |
| `GET`    | `/config/list`                                                  | List all configs (scoped by role) | ✅    |
| `GET`    | `/config/get?service=<name>`                                    | Fetch configuration               | ✅    |
| `POST`   | `/config/update`                                                | Create or update configuration    | ✅    |
| `GET`    | `/config/versions?name=<service>`                               | List historical versions          | ✅    |
| `GET`    | `/config/diff?service=<name>&version1_id=<id>&version2_id=<id>` | Compare two versions (JSON diff)  | ✅    |
| `POST`   | `/config/rollback?service=<name>&version_id=<id>`               | Roll back to a previous version   | ✅    |
| `DELETE` | `/config/delete?service=<name>`                                 | Delete configuration              | ✅    |
| `GET`    | `/config/health`                                                | Health check (DB connectivity)    | ❌    |

---

### 🔐 Role-Based Access Control

| Role    | Permissions                          |
| ------- | ------------------------------------ |
| `admin` | Full access to all configs and users |
| `user`  | Limited to own configurations        |

Admins can perform rollback, version comparison, and deletions for any user by specifying a `target_user_id` query param.

---

## 🧾 Audit Logging with Celery

Every major action — registration, login, update, retrieval, rollback, and deletion — is asynchronously logged using **Celery tasks**.

If Redis or Celery is unavailable, the app automatically falls back to synchronous logging to avoid data loss.

All logs are stored under:

```
app/logs/config_logs.log
```

---

## 🧰 Tech Stack

| Layer                    | Technology              |
| ------------------------ | ----------------------- |
| **Language**             | Python 3.11             |
| **Framework**            | FastAPI                 |
| **Database**             | PostgreSQL              |
| **ORM**                  | SQLAlchemy              |
| **Migrations**           | Alembic                 |
| **Auth**                 | JWT + Token Revocation  |
| **Async Tasks**          | Celery + Redis          |
| **Containerization**     | Docker + Docker Compose |
| **Monitoring (planned)** | Prometheus + Grafana    |

---

## 🗂️ Project Structure

```
ConfigSync/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   └── routes_config.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── crud.py
│   │   ├── database.py
│   │   └── models.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   └── logger.py
│   ├── logs/
│   │   └── config_logs.log
│   └── schemas/
│       ├── auth_schema.py
│       └── config_schema.py
├── alembic/
│   ├── env.py
│   └── versions/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start (Docker Compose)

```bash
# 1. Build and start all services
docker-compose up --build

# 2. Run in background
docker-compose up -d

# 3. View Celery logs
docker-compose logs -f worker

# 4. Stop containers
docker-compose down
```

*(PostgreSQL data persists via the named volume `configsync_data`.)*

---

## 🔬 API Testing Examples

### Register a New User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@mail.com", "password": "secret123"}'
```

### Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -F "username=alice" \
  -F "password=secret123"
```

### Update or Create a Config

```bash
curl -X POST "http://localhost:8000/config/update" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "payment-service", "config": {"TIMEOUT": 30, "URL": "https://api.example.com"}}'
```

### Diff Between Two Versions

```bash
curl "http://localhost:8000/config/diff?service=payment-service&version1_id=2&version2_id=4" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Rollback to a Previous Version

```bash
curl -X POST "http://localhost:8000/config/rollback?service=payment-service&version_id=2" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Delete a Config

```bash
curl -X DELETE "http://localhost:8000/config/delete?service=payment-service" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## 🔐 Environment Variables

| Variable       | Description                           | Default                                                 |
| -------------- | ------------------------------------- | ------------------------------------------------------- |
| `DATABASE_URL` | PostgreSQL connection URI             | `postgresql://configsync:configsync@db:5432/configsync` |
| `SECRET_KEY`   | JWT signing key                       | `supersecretjwtkey`                                     |
| `API_KEY`      | Service-to-service authentication key | `supersecretkey`                                        |
| `REDIS_URL`    | Redis connection URI                  | `redis://redis:6379/0`                                  |
| `PROJECT_NAME` | Display name for API                  | `ConfigSync`                                            |

---

## 💡 Why This Project Matters

Modern microservice systems need reliable, auditable, and versioned configuration control.
**ConfigSync** provides a developer-friendly internal alternative to **AWS Parameter Store** or **HashiCorp Vault**, offering:

* Centralized configuration APIs
* Full versioning and rollback
* Asynchronous audit logging
* Containerized, cloud-ready deployment

---

## 💬 Resume Highlight

> **Built “ConfigSync” — a FastAPI-based configuration management system with JWT authentication, versioning, rollback, and Celery + Redis for asynchronous logging. Containerized via Docker Compose with PostgreSQL persistence and role-based access control.**

---

## 👨‍💻 Author

**Aditya S Joshi**
Backend & Cloud-Native Developer
*“Clean, minimal, and production-minded engineering.”*