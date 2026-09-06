# Railway Deployment Fix — v2

## Root cause from Railway build log

The frontend build failed at Vite config resolution:

`Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@tailwindcss/vite' imported from /build/frontend/vite.config.ts`

The project already declared the package, but the production build was still resolving the Vite config without a guaranteed build-time dependency installation.

## Changes in v2

1. Moved `@tailwindcss/vite` and `tailwindcss` into `frontend/package.json` `dependencies` so the Tailwind Vite integration is treated as a required application build dependency.
2. Updated the Docker build install step to explicitly use `--include=dev` so all Vite/TypeScript build tooling is installed during the image build.
3. Added a dependency-resolution gate immediately after npm install:
   `node -e "require.resolve('@tailwindcss/vite')"`
   This makes dependency problems fail at the correct step instead of producing a misleading Vite build error later.
4. Kept the existing Tailwind v4 + Vite integration intact (`@import "tailwindcss"` and `tailwindcss()` plugin).

## Deploy

Push the contents of this package to the GitHub repository connected to Railway, then redeploy.

Do not manually edit individual source files.
