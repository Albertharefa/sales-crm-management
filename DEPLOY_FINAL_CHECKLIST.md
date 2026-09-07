# SALES CRM MANAGEMENT — FINAL DEPLOYMENT CHECKLIST

Railway Variables:
- MONGO_URL = MongoDB Atlas connection string
- DB_NAME = sales_crm
- ADMIN_EMAIL = production admin email
- ADMIN_PASSWORD = strong production password
- COOKIE_SECURE = true
- CORS_ORIGINS = explicit origins only when frontend is separate
- SEED_DEMO_DATA = false for real production

Deployment:
1. Push/upload this project to the GitHub repository connected to Railway.
2. Railway builder: Dockerfile.
3. Health check: /health.
4. Verify /health returns database=ok.
5. Verify /docs exposes /api routes.
6. Login with ADMIN_EMAIL / ADMIN_PASSWORD.
