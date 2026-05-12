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

Create a new user account. Returns 409 if the email or username is already taken.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "strongpassword",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe"
}
```

Rate limited to **5 requests / minute** per IP.

---

### `POST /auth/login`

Authenticate and receive tokens.

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
  "refresh_token": "abc123...",
  "token_type": "bearer"
}
```

- The **access token** is a short-lived JWT (15 min). Send it in the `Authorization: Bearer <token>` header on protected routes.
- The **refresh token** is a long-lived opaque token (30 days). It is returned in the response body **and** set as an `HttpOnly; Secure; SameSite=Strict` cookie on the `/auth` path.
  - **Web clients** can rely on the cookie — the browser sends it automatically to `/auth/refresh`.
  - **Mobile clients** should read `refresh_token` from the body and store it in Keychain (iOS) / Keystore (Android).

Rate limited to **10 requests / minute** per IP.

---

### `POST /auth/refresh`

Rotate the refresh token and obtain a new access token.

Accepts the refresh token from either:
- the `refresh_token` cookie (set automatically by the browser), or
- a JSON body (mobile clients):

```json
{ "refresh_token": "abc123..." }
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

A new `refresh_token` cookie is set on success. The previous refresh token is immediately revoked.

If a previously revoked token is presented (reuse detected), the entire token family is revoked and the user must log in again.

---

### `POST /auth/logout`

Revoke all refresh tokens for the authenticated user and clear the cookie.

**Headers:** `Authorization: Bearer <access_token>`

Returns `204 No Content`.

---

### `GET /auth/me`

Returns the authenticated user's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "id": "664f...",
  "email": "user@example.com",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```
