# DEPLOY TO RAILWAY — QUICK GUIDE

## 1. GitHub

Upload/push the contents of this folder to the repository connected to Railway.

Do NOT upload:
- `.env`
- real passwords
- `OPENAI_API_KEY`
- `node_modules`
- `frontend/dist`

## 2. Railway Variables

Set:

```text
MONGO_URL=<MongoDB connection string>
DB_NAME=sales_crm
ADMIN_EMAIL=<your admin email>
ADMIN_PASSWORD=<strong password, minimum 8 characters>
COOKIE_SECURE=true
CORS_ORIGINS=
OPENAI_API_KEY=<optional>
OPENAI_MODEL=gpt-5.4
```

For a separate frontend development server, the Vite proxy already sends `/api`
to `http://localhost:8001`.

## 3. Deploy

Railway reads `railway.toml`, builds the root `Dockerfile`, and starts one
service containing both the React application and FastAPI API.

## 4. Verify

Open:

- `/` → CRM application
- `/login` → login
- `/health` → healthy/degraded status
- `/docs` → Swagger

Expected:

```json
{
  "status": "healthy",
  "application": "Sales CRM Management",
  "database": "connected"
}
```

## 5. Admin login

The first startup creates the configured `ADMIN_EMAIL` as `SUPER_ADMIN`.
If the account already exists, the configured `ADMIN_PASSWORD` is synchronized
on startup.

Change `ADMIN_PASSWORD` in Railway Variables when you intentionally want to
rotate the bootstrap password.

## Architecture

```text
Railway HTTPS
     |
     +-- /              React CRM SPA
     +-- /api/*         FastAPI compatibility API
     +-- /docs          Swagger
     +-- /health        Health check
     |
     +-- MongoDB        External MongoDB
```
