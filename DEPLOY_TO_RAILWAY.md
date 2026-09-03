# Sales CRM Management — Railway Production Deployment

## Repository layout

The GitHub repository root MUST contain:

- `Dockerfile`
- `railway.toml`
- `backend/`
- `frontend/`

Do not put these inside an extra nested `sales-crm-management-production/` directory.

## Railway variables

Required:
- `MONGO_URL`
- `DB_NAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

Recommended:
- `COOKIE_SECURE=true`
- `CORS_ORIGINS=`
- `OPENAI_API_KEY=`
- `OPENAI_MODEL=gpt-5.4`

## Deploy

1. Extract the ZIP.
2. Upload the **contents** of the extracted folder to the root of the GitHub repository connected to Railway.
3. Commit and push.
4. Railway should detect the root `Dockerfile` and build the single-service image.
5. Open the generated Railway domain.

## Expected URLs

- `/` → React CRM dashboard
- `/login` → CRM login
- `/docs` → Swagger
- `/redoc` → ReDoc
- `/health` → health check
- `/api/*` → frontend-compatible API
- `/customers`, `/pipeline`, `/activities`, `/quotations`, etc. → public API routes

## If Railway says "Failed to build an image"

Open **Build Logs** (not Deploy Logs) and inspect the first red error. The most important check is that `Dockerfile` is in the repository root.

## Important

Never commit real `.env` files or production secrets to GitHub.
