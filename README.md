# FastAPI boilerplate

A small backend starter to ship APIs faster: **FastAPI** + **MongoDB** (Motor), a ready-made **auth / user** module, and **Docker** for local full-stack runs and production-style deployment.

## Create a new project from this boilerplate

```bash
bash <(curl -sSL https://raw.githubusercontent.com/johnOfGod33/fastapi-boilerplate/main/setup.sh)
```

The script will interactively ask for the project name, description, destination directory, and configure `.env.dev` from `.env.example`. A fresh git repository is initialized at the end.

You can also pass arguments directly:

```bash
bash setup.sh --name my-api --dest ~/projects/my-api
```

## What you get

- **User module** — Registration, login, token refresh, logout, and a protected `GET /auth/me` endpoint; password hashing with Argon2.
- **JWT + Refresh token** — Short-lived access token (15 min) paired with a long-lived opaque refresh token (30 days, SHA-256 hashed in DB). Rotation on every refresh with family-based reuse detection (full revocation on theft). Refresh token delivered as an `HttpOnly` cookie (web) and in the response body (mobile).
- **Rate limiting** — `slowapi` guards `/auth/register` (5/min) and `/auth/login` (10/min).
- **MongoDB** — Async client wired in the app lifespan, shared DB accessor for routes, unique indexes on `email` and `username`, TTL index on `refresh_tokens.expires_at`, and a `/health` check that pings MongoDB.
- **Docker** — Multi-stage image (Python 3.13), Compose stacks for **detached “prod-like”** runs and **interactive dev** (hot reload + bind-mounted `app/`).
- **Quality hooks** — Tests (pytest), lint/format tooling in dependencies, and CI workflows under `.github/workflows/` (and optional GitLab CI if you use it).

Interactive docs: `http://localhost:8000/docs` once the API is running.

## Requirements

- Python **3.13+** (matches the Dockerfile)
- **Docker** and **Docker Compose** (optional but recommended for DB + API together)

## Configuration

Copy the example env file and adjust values:

```bash
cp .env.example .env
```

| Variable                               | Purpose                                                                                                                                                                                                                                                          |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MONGODB_URI`                          | MongoDB connection string. Use `mongodb://localhost:27017` when you run Uvicorn on the host and MongoDB locally. When **both API and MongoDB run in Docker Compose**, the host in the URI must be the Compose service name: `mongodb://mongo:27017` (see below). |
| `MONGODB_DB_NAME`                      | Database name                                                                                                                                                                                                                                                    |
| `JWT_SECRET`                           | Signing secret for access tokens (use a strong value in production)                                                                                                                                                                                              |
| `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` | JWT settings — access token expires in 15 minutes by default                                                                                                                                                                                                     |
| `REFRESH_TOKEN_EXPIRE_DAYS`            | Refresh token lifetime in days (default: 30)                                                                                                                                                                                                                     |

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

This uses `docker-compose.dev.yml` and sets `MONGODB_URI=mongodb://mongo:27017` for the API container so it talks to the `mongo` service on the Compose network.

**Deployment-style** — API and MongoDB in the background (no reload):

```bash
make infra
```

Uses `docker-compose.yml`. Ensure your `.env` sets `MONGODB_URI=mongodb://mongo:27017` when running the full stack in Compose so the API does not point at `localhost` inside the container.

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
infra/                 # Example infrastructure (e.g. CloudFormation)
```

Rename the app metadata in `app/main.py` (`title`, `description`, `version`) and extend `app/modules/` with your own domains following the same pattern.

---

Use this repo as a template: replace branding, tighten security defaults for production, and grow modules alongside your product.
