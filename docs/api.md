# API Reference

Full interactive documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) when the API is running.

## Health

### `GET /health`

Returns the API status and MongoDB connectivity.

```json
{ "status": "ok", "database": "connected" }
```

## Auth

### `POST /auth/register`

Create a new user account.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "strongpassword"
}
```

### `POST /auth/login`

Authenticate and receive a JWT access token.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "strongpassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### `GET /auth/me`

Returns the authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`
