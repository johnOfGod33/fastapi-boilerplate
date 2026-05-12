# Architecture

## Project layout

```
app/
  main.py              # FastAPI app, lifespan, routes registration
  core/
    config.py          # Settings loaded from environment variables
    database.py        # MongoDB async client, shared DB accessor, index creation
    security.py        # Password hashing (Argon2), JWT creation/verification
    limiter.py         # slowapi rate-limiter singleton
    custom_document.py # Base document helpers
  modules/
    user/              # User domain: models, service, router
  requirements.txt
docker-compose.yml     # API + MongoDB (detached / prod-like)
docker-compose.dev.yml # Dev: hot reload + app/ volume mount
Dockerfile             # Multi-stage Python 3.13 image
```

## Request lifecycle

```
Client → FastAPI router → dependency injection → service layer → MongoDB
```

- **Routers** handle HTTP concerns (request parsing, response serialization).
- **Services** contain business logic and call the database.
- **Dependencies** (`app/dependencies.py`) provide shared objects (DB, current user).

## Authentication

JWT + opaque refresh token flow:

1. `POST /auth/register` — creates user, hashes password with Argon2, enforces unique email and username.
2. `POST /auth/login` — verifies password and `is_active` flag, returns a signed JWT (15 min) and a refresh token (30 days). The refresh token is SHA-256 hashed before storage. It is delivered as an `HttpOnly` cookie and in the response body.
3. `POST /auth/refresh` — validates the refresh token, revokes it, and issues a new one (rotation). If a revoked token is reused, the entire token family is revoked (theft detection).
4. `POST /auth/logout` — revokes all refresh tokens for the user and deletes the cookie.
5. Protected routes use the `get_current_user` dependency which decodes the JWT.

### MongoDB collections

| Collection       | Purpose                                              |
| ---------------- | ---------------------------------------------------- |
| `users`          | User documents — unique indexes on `email`, `username` |
| `refresh_tokens` | Active refresh tokens — unique index on `token_hash`, TTL index on `expires_at` (auto-deleted by MongoDB) |

## Adding a new module

```
app/modules/
  my_feature/
    __init__.py
    models.py    # Pydantic schemas (request / response)
    service.py   # Business logic + DB calls
    router.py    # APIRouter with routes
```

Then register the router in `app/main.py`:

```python
from app.modules.my_feature.router import router as my_feature_router
app.include_router(my_feature_router, prefix="/my-feature")
```
