# ⚙️ ConfigSync — Centralized Configuration Management System

**ConfigSync** is a self-hosted **configuration management platform** built with **FastAPI**, designed to securely manage and version environment variables and configuration files across microservices.

It provides a single API for **storing**, **fetching**, **comparing**, **deleting**, and **rolling back** configurations — backed by **PostgreSQL** persistence, **Celery + Redis** asynchronous audit logging, and a **comprehensive automated test suite** with 91% coverage.

---

## 🚀 Features

### ✅ Core Functionality

* **FastAPI backend** with modular architecture
* **PostgreSQL + SQLAlchemy** for reliable data storage
* **Alembic** migrations for schema versioning
* **JWT-based authentication** with **role-based access control** (admin/user)
* **Token revocation** for secure session management
* **Full configuration versioning and rollback** support
* **JSON diffing** to compare any two historical versions
* **Celery + Redis** for asynchronous audit logging
* **Containerized** using Docker + Docker Compose
* **Persistent PostgreSQL volumes** for data durability
* **CI pipeline** with **pytest + coverage reports** for continuous testing

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

### 🔄 Example Flow

1. A user sends a `POST /config/update` request.
2. FastAPI updates the configuration in **PostgreSQL**, creating a new version.
3. A **Celery task** asynchronously logs the change.
4. The Celery worker writes structured entries into `app/logs/config_logs.log`.
5. The API returns immediately — ensuring responsive performance even under load.

---

## 🧩 Key API Endpoints

| Method   | Endpoint                                                        | Description                              | Auth |
| -------- | --------------------------------------------------------------- | ---------------------------------------- | ---- |
| `POST`   | `/auth/register`                                                | Register a new user                      | ❌    |
| `POST`   | `/auth/login`                                                   | Login and obtain JWT                     | ❌    |
| `POST`   | `/auth/logout`                                                  | Revoke JWT token (logout)                | ✅    |
| `GET`    | `/config/list`                                                  | List all configurations (scoped by role) | ✅    |
| `GET`    | `/config/get?service=<name>`                                    | Fetch configuration by service           | ✅    |
| `POST`   | `/config/update`                                                | Create or update configuration           | ✅    |
| `GET`    | `/config/versions?name=<service>`                               | View configuration history               | ✅    |
| `GET`    | `/config/diff?service=<name>&version1_id=<id>&version2_id=<id>` | Compare two versions (JSON diff)         | ✅    |
| `POST`   | `/config/rollback?service=<name>&version_id=<id>`               | Roll back to a previous version          | ✅    |
| `DELETE` | `/config/delete?service=<name>`                                 | Delete configuration                     | ✅    |
| `GET`    | `/config/health`                                                | Health check (DB + Redis status)         | ❌    |

---

### 🔐 Role-Based Access Control

| Role    | Permissions                                 |
| ------- | ------------------------------------------- |
| `admin` | Full access to all users and configurations |
| `user`  | Limited to their own configurations         |

Admins can perform diffing, rollback, or deletions for other users using `target_user_id` query parameters.

---

## 🧾 Asynchronous Audit Logging

All configuration and authentication actions — **register, login, update, delete, rollback** — are logged through **Celery background tasks**.

If Celery or Redis are temporarily unavailable, the system gracefully falls back to synchronous logging to avoid data loss.

Logs are written to:

```
app/logs/config_logs.log
```

---

## 🧪 Continuous Integration & Testing

ConfigSync uses **GitHub Actions CI** to automatically test and validate every commit.

| Metric                | Result                                     |
| --------------------- | ------------------------------------------ |
| **Tests executed**    | 37                                         |
| **Coverage**          | 91%                                        |
| **Warnings**          | 1 (Pydantic v2 migration notice)           |
| **CI Runtime**        | ~7m 30s                                    |
| **Testing Toolchain** | `pytest`, `pytest-cov`, `asyncio`, `anyio` |

Example coverage summary:

```
TOTAL 531 statements, 49 missed → 91% coverage
All 37 tests passed ✅
```

Tests cover:

* Authentication & JWT lifecycle
* Role-based access enforcement
* CRUD operations for configurations
* Version history, diffing, and rollback
* Admin override capabilities
* Token revocation and invalid token handling

---

## 🧰 Tech Stack

| Layer                    | Technology              |
| ------------------------ | ----------------------- |
| **Language**             | Python 3.11             |
| **Framework**            | FastAPI                 |
| **Database**             | PostgreSQL              |
| **ORM**                  | SQLAlchemy              |
| **Migrations**           | Alembic                 |
| **Auth**                 | JWT + Revocation        |
| **Async Tasks**          | Celery + Redis          |
| **Containerization**     | Docker + Docker Compose |
| **Testing**              | pytest + coverage       |
| **CI/CD**                | GitHub Actions          |
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
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   └── config_schema.py
│   ├── logs/
│   │   └── config_logs.log
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_config.py
│   └── test_versioning.py
├── alembic/
│   ├── env.py
│   └── versions/
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## ⚡ Quick Start (Docker Compose)

```bash
# 1️⃣ Build and start services
docker-compose up --build

# 2️⃣ Run in background
docker-compose up -d

# 3️⃣ View Celery worker logs
docker-compose logs -f worker

# 4️⃣ Stop and clean up
docker-compose down
```

*(PostgreSQL data persists in the `configsync_data` volume.)*

---

## 🔬 API Testing Examples

### Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@mail.com", "password": "secret123"}'
```

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -F "username=alice" -F "password=secret123"
```

### Create or Update Config

```bash
curl -X POST "http://localhost:8000/config/update" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "payment-service", "config": {"TIMEOUT": 30, "URL": "https://api.example.com"}}'
```

### Compare Two Versions

```bash
curl "http://localhost:8000/config/diff?service=payment-service&version1_id=2&version2_id=4" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Roll Back

```bash
curl -X POST "http://localhost:8000/config/rollback?service=payment-service&version_id=2" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Delete Config

```bash
curl -X DELETE "http://localhost:8000/config/delete?service=payment-service" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## 🔐 Environment Variables

| Variable       | Description                | Default                                                 |
| -------------- | -------------------------- | ------------------------------------------------------- |
| `DATABASE_URL` | PostgreSQL connection URI  | `postgresql://configsync:configsync@db:5432/configsync` |
| `SECRET_KEY`   | JWT signing key            | `supersecretjwtkey`                                     |
| `API_KEY`      | Service authentication key | `supersecretkey`                                        |
| `REDIS_URL`    | Redis connection URI       | `redis://redis:6379/0`                                  |
| `PROJECT_NAME` | Display name for API       | `ConfigSync`                                            |

---

## 💡 Why ConfigSync Matters

Modern teams juggle multiple environments and microservices — ConfigSync ensures:

* **Centralized configuration access**
* **Version control & rollback safety**
* **Asynchronous, auditable logging**
* **Production-ready containerization**
* **Full CI/CD compatibility**

It acts as a lightweight, self-hosted alternative to **AWS Parameter Store** or **HashiCorp Vault**, tailored for smaller or internal developer teams.

---

## 💬 Resume Highlight

> **Built “ConfigSync” — a FastAPI-based configuration management system with JWT auth, versioning, rollback, and Celery + Redis asynchronous logging. Added CI integration with pytest coverage (91%), Alembic migrations, and Dockerized PostgreSQL persistence with role-based access control.**

---

## 👨‍💻 Author

**Aditya S Joshi**
Backend & Cloud-Native Developer
*“Clean, minimal, and production-minded engineering.”*