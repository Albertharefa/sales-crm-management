# RBAC V2 Production Audit Checklist

Baseline: RBAC V2

## Model
- Role: SUPER_ADMIN / SALES_MANAGER / SALES
- Action: VIEW / CREATE / EDIT / DELETE / APPROVE / EXPORT / UPDATE / MANAGE / RESET_PASSWORD
- Scope: ALL / TEAM / SELF

## Required invariants
- SUPER_ADMIN: unrestricted business and administration access.
- SALES_MANAGER: team-scoped business data; no cross-manager data access.
- SALES: self-scoped business data; no access to other sales users' records.
- UI visibility must match backend authorization.
- Direct API/URL access must be denied when permission or scope is insufficient.
- Export must be explicitly authorized.
- Approval must be explicitly authorized.
- Delete must be explicitly authorized and must not bypass scope.
- Users and Audit Log must respect administrative/team scope.
- Target Sales: SUPER_ADMIN=ALL, SALES_MANAGER=TEAM, SALES=SELF.

## Regression checks
1. Login and /me succeed for each role.
2. Dashboard loads without authorization errors.
3. Target Sales scope is correct for each role.
4. Sales Team is unavailable to SALES and team-scoped for SALES_MANAGER.
5. Unauthorized endpoints return 403 rather than leaking data.
6. Export endpoints require export permission.
7. Delete endpoints require delete permission.
8. Approval endpoints require approve permission.
9. Audit Log cannot be accessed by SALES.
10. User management cannot be accessed by SALES.

This document is a QA contract only; it does not grant permissions and does not replace backend enforcement.
