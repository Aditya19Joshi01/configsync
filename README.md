# ⚙️ ConfigSync — Centralized Configuration Management System

**ConfigSync** is a self-hosted configuration management platform built with **FastAPI**, designed to centralize and securely manage environment variables and configuration files for multiple microservices.

It eliminates scattered `.env` files, ensures **consistent configuration across environments**, and provides a single API for **storing**, **fetching**, **versioning**, and **synchronizing** configurations.

---

## 🚀 Features

### ✅ Core Functionality

* **FastAPI backend** with modular, clean architecture
* **PostgreSQL** for persistent, relational configuration storage
* **Alembic** for **database migrations and version control**
* **User authentication** (JWT-based) with **admin role-based access**
* **API key authentication** for external service access
* **Containerized** with Docker + Docker Compose
* **Hot reloads** via bind mounts
* **Persistent volumes** for Postgres data

---

## 🧩 API Endpoints

| Method | Endpoint                     | Description                       | Auth Required |
| ------ | ---------------------------- | --------------------------------- | ------------- |
| `POST` | `/auth/signup`               | Register a new user               | ❌             |
| `POST` | `/auth/login`                | Login and get JWT                 | ❌             |
| `GET`  | `/config/get?service=<name>` | Fetch configuration for a service | ✅             |
| `POST` | `/config/update`             | Create or update configuration    | ✅             |
| `GET`  | `/`                          | Health check                      | ❌             |

### 🔐 Role-Based Access Control

| Role    | Permissions                                              |
| ------- | -------------------------------------------------------- |
| `admin` | Full access to create, update, delete any config or user |
| `user`  | Can only access and modify their own configurations      |

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
| **Task Queue (planned)** | Celery + Redis          |
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

### 1️⃣ Build and start containers

```bash
docker-compose up --build
```

### 2️⃣ Run in background

```bash
docker-compose up -d
```

### 3️⃣ View logs

```bash
docker-compose logs -f backend
```

### 4️⃣ Stop containers

```bash
docker-compose down
```

*(Postgres data persists because of named volume `configsync_data`.)*

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

### 🔸 Update or Create a Config

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
| `DATABASE_URL` | Postgres connection URI               | `postgresql://configsync:configsync@db:5432/configsync` |
| `SECRET_KEY`   | JWT signing key                       | `supersecretkey`                                        |
| `API_KEY`      | Service-to-service authentication key | `supersecretkey`                                        |
| `PROJECT_NAME` | Display name for API                  | `ConfigSync`                                            |

---

## 🧵 Volumes and Mounts

| Container | Mount Type   | Host Path / Volume                             |
| --------- | ------------ | ---------------------------------------------- |
| `backend` | Bind Mount   | `./app` → `/app/app`                           |
| `db`      | Named Volume | `configsync_data` → `/var/lib/postgresql/data` |

---

## ⚙️ Upcoming Enhancements

| Feature                             | Description                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------- |
| 🧵 **Celery + Redis integration**   | For asynchronous config sync, background update tasks, and change notifications |
| 🪣 **Config version history**       | Track who changed what and when                                                 |
| 📊 **Prometheus + Grafana metrics** | Monitor config usage, last update timestamps, fetch frequency                   |
| 🧪 **Pytest test suite**            | Automated testing for CRUD and auth endpoints                                   |
| ☁️ **Terraform simulation**         | Infrastructure-as-code setup for reproducibility                                |

---

## 💡 Why This Project Matters

Modern microservice architectures rely on distributed configurations.
**ConfigSync** provides a lightweight, developer-friendly way to ensure consistent, auditable configuration management — functioning like an **internal AWS Parameter Store or HashiCorp Vault lite**.

---

## 💬 Resume Highlight

> **Built “ConfigSync” — a FastAPI-based, self-hosted configuration management system with JWT authentication, Alembic database migrations, and Dockerized PostgreSQL persistence; designed to centralize environment variables across microservices and eliminate configuration drift.**

---

## 👨‍💻 Author

**Aditya S Joshi**
Backend & Cloud-Native Developer
*“Clean, minimal, and production-minded engineering.”*