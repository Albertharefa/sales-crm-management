# CRM Sales Management Production — Test Handoff

See `memory/SPEC.md` for the canonical living specification.

Seed facts: 3 users, 50 customers, 50 opportunities, 100 activities, 50 tasks, 50 products, 30 quotations, 20 purchase orders. The reference-compatible routes are `/`, `/customers`, `/pipeline`, `/activities`, `/quotations`, `/purchase-orders`, `/order-monitoring`, `/sales-team`, `/audit-log`, `/users`, `/products`, and `/settings`.

Primary happy path: login as Super Admin, verify dashboard KPIs, create a customer, confirm it appears in the server-paginated table, and logout.