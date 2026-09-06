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


## Production environment variables

Use these values in Railway Variables:

- `MONGO_URL` — MongoDB connection string
- `DB_NAME` — production database name
- `ADMIN_EMAIL` — initial Super Admin email
- `ADMIN_PASSWORD` — initial Super Admin password
- `COOKIE_SECURE=true` — keep enabled on Railway HTTPS
- `ADMIN_FORCE_PASSWORD_RESET=false` — only set to `true` when you intentionally want to rotate the admin password on the next deploy
- `CORS_ORIGINS=` — leave empty for the normal same-origin deployment; use a comma-separated list only for trusted external origins
- `OPENAI_API_KEY=` — optional, for AI Copilot if your AI integration requires it
- `OPENAI_MODEL=gpt-5.4` — optional

### Important after deployment

1. Open `/health` and confirm `"status": "healthy"` and `"database": "connected"`.
2. Open `/docs` and confirm both `/api/...` and legacy routes are present.
3. Open the Railway root `/`; it should display the React CRM login/dashboard, not the JSON API status response.
4. Test login, customer search, pipeline, quotation PDF, PO monitoring, and AI Copilot.
5. If you change `ADMIN_PASSWORD`, do not expect an existing password to change unless `ADMIN_FORCE_PASSWORD_RESET=true`.
