# {{project_name}}

{{project_description}}

## Overview

This API is built with **FastAPI** + **MongoDB** (async via Motor), containerized with Docker.

- Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Getting started

```bash
# Install dependencies
make install

# Start the API (requires MongoDB)
make run-dev

# Or start everything with Docker
make infra-dev
```

## Modules

| Module | Description |
|--------|-------------|
| `user` | Registration, login (JWT), protected profile endpoint |

Extend the API by adding new modules under `app/modules/` following the same pattern.
