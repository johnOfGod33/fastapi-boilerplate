# Architecture

## Project layout

```
app/
  main.py              # FastAPI app, lifespan, routes registration
  core/
    config.py          # Settings loaded from environment variables
    database.py        # MongoDB async client, shared DB accessor
    security.py        # Password hashing (Argon2), JWT creation/verification
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

JWT-based authentication using `python-jose`:

1. `POST /auth/register` — creates user, hashes password with Argon2.
2. `POST /auth/login` — verifies password, returns a signed JWT.
3. Protected routes use the `get_current_user` dependency which decodes the token.

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
