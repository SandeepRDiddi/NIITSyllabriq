# Docker Deployment Changes

## Section 1 — Understanding Docker Images vs Containers

```
SOURCE CODE + Dockerfile
        │
        │  docker build
        ▼
    DOCKER IMAGE
    (a sealed, portable snapshot —
     like a ZIP file of the entire
     runtime environment)
        │
        │  docker run  (or docker compose up)
        ▼
  DOCKER CONTAINER
  (a live, running instance of the image —
   like a running program launched from that ZIP)
```

Every time source code or a Dockerfile changes, the image must be rebuilt (`docker compose build`) before the change takes effect. Simply restarting a container reuses the old image.

---

## Section 2 — How the Backend Image is Built

**File:** `Dockerfile`

### Build Steps (`docker compose build`)

1. Pulls `python:3.11-slim` base image
2. Copies `pyproject.toml` and installs all dependencies (FastAPI, SQLModel, Alembic, Uvicorn, etc.)
3. Copies `app/` source code and `alembic/` migration scripts
4. Creates required storage directories

### Startup Sequence (`docker compose up`)

```
alembic upgrade head   → connects to PostgreSQL and applies pending migrations
uvicorn app.main:app   → starts the FastAPI server on port 8000
```

---

## Section 3 — How the Frontend Image is Built

**File:** `frontend/Dockerfile` — Modified

### Stage 1 (Node.js environment)

```
npm ci        → installs React, TypeScript, Vite, all frontend dependencies
npm run build → compiles everything into /frontend/dist/
                (a folder of plain .html, .js, .css files)
```

### Stage 2 (Nginx environment)

- Only the `/dist` folder is copied across
- Node.js is completely discarded
- Result: a tiny image (~50 MB) containing only Nginx + compiled files

---

## Section 4 — New File Created: `nginx/nginx.conf`

Created to route internet traffic to the right service.

### Before (without a reverse proxy)

- Frontend was only reachable at port `8080`
- Backend API was only reachable at port `8000`
- Both ports would need to be open on the firewall
- No single entry point

### Traffic Flow

```
http://localhost/               → frontend container (React app)
http://localhost/api/auth/login → backend container (FastAPI)  [/api/ stripped]
http://localhost/docs           → backend container
http://localhost/api/health     → backend container
```

---

## Section 5 — Modified File: `docker-compose.yml`

### Change 1 — Removed the obsolete `version` field

```yaml
# REMOVED
version: "3.9"
```

Docker warned: `"the attribute version is obsolete, it will be ignored"`. Modern Docker Compose (v2) does not use this field.

---

### Change 2 — Added healthcheck to postgres and `condition: service_healthy` to backend

**Problem discovered during testing:**

```
psycopg.OperationalError: connection failed: Connection refused
Is the server running on that host and accepting TCP/IP connections?
```

`depends_on: - postgres` only tells Docker to *start* the postgres container before the backend. It does not wait for PostgreSQL to be ready to accept connections. PostgreSQL takes 3–8 seconds to initialize its data files — the backend was starting during that window and crashing.

```yaml
# ADDED to postgres service
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  interval: 5s       # Check every 5 seconds
  timeout: 5s        # Give up on a check after 5 seconds
  retries: 10        # Try up to 10 times before declaring unhealthy
  start_period: 10s  # Don't count failures in the first 10 seconds

# CHANGED in design-automation service
depends_on:
  postgres:
    condition: service_healthy   # Wait until pg_isready returns success
```

`pg_isready` is a utility built into the official postgres Docker image. It probes the PostgreSQL port and returns success only when the database is genuinely accepting connections.

---

### Change 3 — Added frontend service

The frontend had a Dockerfile but was never in `docker-compose.yml`. It had to be built and run manually as a separate operation.

```yaml
frontend:
  build:
    context: .                        # Build context is the project root
    dockerfile: frontend/Dockerfile   # Use the frontend-specific Dockerfile
    args:
      VITE_API_BASE_URL: /api         # Passed into the Dockerfile as ARG
  depends_on:
    - design-automation
```

---

### Change 4 — Added nginx service

```yaml
nginx:
  image: nginx:1.27-alpine
  ports:
    - "80:80"                          # Only port exposed to the outside world
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    # Mounts our config file into the nginx container
    # :ro = read-only — the container cannot modify it
  depends_on:
    - frontend
    - design-automation
```

---

### Change 5 — Replaced hardcoded secrets with `.env` variable substitution

```yaml
# Values come from the .env file at runtime
JWT_SECRET_KEY: ${JWT_SECRET_KEY}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
PRIMARY_REVIEWERS: ${PRIMARY_REVIEWERS}
```

Docker Compose automatically reads a file named `.env` in the same directory and substitutes `${VARIABLE}` placeholders.

---

### Change 6 — Removed direct port exposure from postgres and backend

```yaml
# REMOVED from postgres
ports:
  - "5432:5432"

# REMOVED from design-automation
ports:
  - "8000:8000"
```

With these port mappings present, the database and API were directly reachable from the internet, bypassing NGINX entirely. Removing them means all four containers communicate only through Docker's internal private network. The only way in from outside is through NGINX on port 80.

---

### `.env` Changes

```env
# ADDED — required by the postgres container and by the DATABASE_URL
POSTGRES_USER=niit
POSTGRES_PASSWORD=niit
POSTGRES_DB=niit_design_automation

# CHANGED — default was development, template is for server deployment
ENVIRONMENT=production

# CHANGED — added http://localhost (port 80 via NGINX, replaces port 3000)
ALLOWED_ORIGINS=http://localhost,http://localhost:5173,http://127.0.0.1:5173
```

---

## Section 6 — Modified File: `pyproject.toml`

`pyproject.toml` is the Python project's dependency manifest. When the backend Docker image is built, `pip install .` reads this file and installs every listed package.

**Error discovered during testing:**

```
ModuleNotFoundError: No module named 'email_validator'
ImportError: email-validator is not installed,
             run `pip install 'pydantic[email]'`
```

The application uses `EmailStr` (Pydantic's validated email type) in `app/schemas/auth.py`. Pydantic requires a separate package called `email-validator` to perform email format validation. It was used in the code but never declared as a dependency, so it was never installed inside the Docker image.

```toml
# ADDED
"email-validator>=2.1.0,<3.0.0",
```

This was a missing dependency bug — the application would fail to start on any fresh Docker installation.

---

## Section 7 — Final State: What `docker compose up -d` Now Does

```
docker compose up -d
        │
        ├── Starts postgres container
        │       └── Runs healthcheck every 5s until pg_isready passes
        │
        ├── Starts design-automation container (waits for postgres healthy)
        │       ├── Runs: alembic upgrade head  (creates/migrates DB tables)
        │       └── Runs: uvicorn app.main:app  (starts API on :8000)
        │
        ├── Starts frontend container
        │       └── Nginx serves compiled React files on :8080
        │
        └── Starts nginx container
                └── Listens on :80
                    ├── /api/* → design-automation:8000
                    └── /*     → frontend:8080
```

---

## Section 8 — Verification After All Changes (Local Test Results)

```
docker compose up -d
[+] up 4/4
 ✔ Container niitsyllabriq-postgres-1          Healthy    6.5s
 ✔ Container niitsyllabriq-design-automation-1 Started    0.5s
 ✔ Container niitsyllabriq-frontend-1          Started    0.6s
 ✔ Container niitsyllabriq-nginx-1             Started
```

```
$ docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

NAMES                                  STATUS                    PORTS
niitsyllabriq-nginx-1                  Up 19 seconds             0.0.0.0:80->80/tcp, [::]:80->80/tcp
niitsyllabriq-frontend-1               Up 20 seconds             80/tcp, 8080/tcp
niitsyllabriq-design-automation-1      Up 20 seconds             8000/tcp
niitsyllabriq-postgres-1               Up 27 seconds (healthy)   5432/tcp
```

All four containers running. Only port 80 exposed externally — all internal traffic flows through Docker's private network.
