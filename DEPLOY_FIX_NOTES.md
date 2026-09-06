# Deployment Fix V3

Fixes Railway frontend build failure where `@tailwindcss/vite` was declared in package.json but was not present in node_modules at build time.

The Docker build now explicitly enables development dependencies and explicitly installs the exact Tailwind packages before resolving them. It also prefers the online npm registry rather than relying on a stale cache.
