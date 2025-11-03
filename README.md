# ⚙️ ConfigSync — Centralized Configuration Management System

**ConfigSync** is a lightweight, self-hosted configuration management service designed to centralize environment variables and configuration files for multiple microservices.  
It eliminates scattered `.env` and `YAML` files across teams and provides a single API to **store**, **fetch**, and **synchronize** configurations.

---

## 🚀 Features (Current Progress)

### ✅ Core Functionality
* **FastAPI backend** for configuration CRUD operations  
* **PostgreSQL** database (containerized) for persistent storage  
* **API key authentication** for secure updates  
* **Declarative Docker Compose setup** for local development  
* **Bind mount for live reloads** — no rebuilds needed during development  
* **Named volume** for persistent Postgres data  
* **Object-oriented, modular code structure** (clean and scalable)

### 🧩 API Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|-----------|--------------|----------------|
| `GET` | `/config/get?service=<name>` | Fetch configuration for a service | ❌ |
| `POST` | `/config/update` | Create or update configuration | ✅ (x-api-key) |
| `GET` | `/` | Health check | ❌ |

---

## 🏗️ Tech Stack

| Layer | Tool |
|-------|------|
| **Language** | Python 3.11 |
| **Framework** | FastAPI |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy |
| **Auth** | API Key (x-api-key header) |
| **Containerization** | Docker + Docker Compose |
| **Configuration** | Environment variables (managed via `.env` or docker-compose) |

---

## 🧰 Project Structure
```

ConfigSync/
├── app/
│   ├── api/
│   │   └── routes\_config.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── crud.py
│   │   ├── database.py
│   │   └── models.py
│   ├── schemas/
│   │   └── config\_schema.py
│   └── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── Alembic/
    ├── versions/
    └── env.py

````

---

## ⚡ Quick Start (Docker Compose)

### 1️⃣ Build and start containers
```bash
docker-compose up --build
````

### 2️⃣ Run in background

```bash
docker-compose up -d
```

### 3️⃣ Check logs

```bash
docker-compose logs -f backend
```

### 4️⃣ Stop containers

```bash
docker-compose down
# Database data persists because it uses a named volume (configsync_data).
```

### 🧪 API Testing Examples

#### **Update or Create a Config**

```bash
curl -X POST "http://localhost:8000/config/update" \
  -H "Content-Type: application/json" \
  -H "x-api-key: supersecretkey" \
  -d '{
    "name": "payment-service",
    "config": {
      "API_URL": "[https://api.example.com](https://api.example.com)",
      "TIMEOUT": 30
    }
  }'
```

#### **Fetch a Config**

```bash
curl "http://localhost:8000/config/get?service=payment-service"
```

#### **Visit Swagger Docs**

👉 **[http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)**

-----

## 🔐 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Database connection string | `postgres://configsync:configsync@db:5432/configsync` |
| `API_KEY` | API key required for updates | `supersecretkey` |
| `PROJECT_NAME` | Service name | `ConfigSync` |

-----

## 📦 Volumes and Mounts

| Container | Mount Type | Host Path / Volume |
|---|---|---|
| `backend` | Bind Mount | `./app` → `/app/app` |
| `db` | Named Volume | `configsync_data` → `/var/lib/postgresql/data` |

-----

## 📈 What’s Next (Upcoming Enhancements)

  * **Prometheus metrics** for monitoring: `config_fetch_count`, `last_update_timestamp`
  * **Grafana dashboard** integration for visualization
  * **JWT-based authentication** (optional alternative to API key)
  * **Config versioning** (track historical changes)
  * **Automated tests** using `pytest` and FastAPI `TestClient`
  * **Terraform simulation** for infrastructure setup

-----

## 🧠 Why This Project Matters

**Configuration drift** is a real issue — even small teams struggle to keep environment variables consistent across services. ConfigSync solves this by centralizing configuration management in a simple, self-hosted, containerized system that feels like a **“mini internal AWS Parameter Store.”**

-----

## 💬 Example Resume Line

> Developed “ConfigSync,” an internal configuration management system that centralizes versioning and synchronization of environment variables across microservices, containerized with Docker and secured with API key authentication.

-----

## 🧑‍💻 Author

Aditya S Joshi  
Backend & Cloud-Native Developer  
*“Clean, minimal, and production-minded engineering.”*