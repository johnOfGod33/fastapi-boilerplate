# {{project_name}}

{{project_description}}

## What you get

- **User module** — Registration, login (JWT), and a protected `GET /auth/me` endpoint; password hashing with Argon2.
- **MongoDB** — Async client wired in the app lifespan, shared DB accessor for routes, and a `/health` check that pings MongoDB.
- **Docker** — Multi-stage image (Python 3.13), Compose stacks for **detached "prod-like"** runs and **interactive dev** (hot reload + bind-mounted `app/`).
- **Quality hooks** — Tests (pytest), lint/format tooling in dependencies, and CI workflows under `.github/workflows/`.

Interactive docs: `http://localhost:8000/docs` once the API is running.

## Requirements

- Python **3.13+** (matches the Dockerfile)
- **Docker** and **Docker Compose** (optional but recommended for DB + API together)

## Configuration

The `.env.dev` file was generated during project setup. Adjust the values as needed:

| Variable | Purpose |
|----------|---------|
| `MONGODB_URI` | MongoDB connection string. Use `mongodb://mongo:27017` when running in Docker Compose. |
| `MONGODB_DB_NAME` | Database name |
| `JWT_SECRET` | Signing secret for access tokens (use a strong value in production) |
| `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` | JWT settings |

## Run locally (without Docker)

Install dependencies and start the API (MongoDB must be reachable at your `MONGODB_URI`):

```bash
make install
make run-dev
```

Other targets:

- `make run` — Uvicorn without reload
- `make test` — Pytest

## Run with Docker

**Development** — API with `--reload`, code mounted from `./app`, plus MongoDB:

```bash
make infra-dev
```

**Deployment-style** — API and MongoDB in the background (no reload):

```bash
make infra
```

API: `http://localhost:8000` · MongoDB port **27017** is published for local tools if needed.

## Project layout

```
app/
  main.py              # FastAPI app, lifespan, routes
  core/                # Config, DB, security helpers
  modules/user/        # User models, service, router
  requirements.txt
docker-compose.yml     # API + MongoDB (detached)
docker-compose.dev.yml # Dev: reload + volume mount
Dockerfile
```

Rename the app metadata in `app/main.py` (`title`, `description`, `version`) and extend `app/modules/` with your own domains following the same pattern.
