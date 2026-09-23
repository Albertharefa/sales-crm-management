# CRM RBAC V2 — Role × Module × Action × Data Scope

## Roles

- `SUPER_ADMIN` — Management / all-data scope (`ALL`)
- `SALES_MANAGER` — team-management scope (`TEAM`)
- `SALES` — personal scope (`SELF`)

## Core actions

- `view`
- `create`
- `edit`
- `delete`
- `approve`
- `export`
- `update`
- `manage`
- `reset_password`

## Policy

| Module | SUPER_ADMIN | SALES_MANAGER | SALES |
|---|---|---|---|
| Dashboard | View / ALL | View / TEAM | View / SELF |
| Customers | View/Create/Edit/Delete/Export / ALL | View/Create/Edit/Delete/Export / TEAM | View/Create/Edit/Export / SELF |
| Sales Pipeline | View/Create/Edit/Delete/Export / ALL | View/Create/Edit/Delete/Export / TEAM | View/Create/Edit/Export / SELF |
| Activities | View/Create/Edit/Delete/Export / ALL | View/Create/Edit/Delete/Export / TEAM | View/Create/Edit/Export / SELF |
| Quotations | View/Create/Edit/Approve/Delete/Export / ALL | View/Create/Edit/Approve/Delete/Export / TEAM | View/Create/Edit/Export / SELF |
| Purchase Orders | View/Create/Edit/Delete/Export / ALL | View/Create/Edit/Delete/Export / TEAM | View/Create/Edit/Export / SELF |
| Order Monitoring | View/Update / ALL | View/Update / TEAM | View/Update / SELF |
| Sales Team | View/Manage/Export / ALL | View / TEAM | — |
| Target Sales | View/Manage / ALL | View/Manage / TEAM | View / SELF |
| Users | View/Create/Edit/Delete/Reset Password / ALL | View / TEAM | — |
| Products | View/Create/Edit/Delete/Export / ALL | View/Export / TEAM | View/Export / SELF |
| Audit Log | View / ALL | View / TEAM | — |
| AI | Use / ALL | Use / TEAM | Use / SELF |
| Uploads | Use / ALL | Use / TEAM | Use / SELF |
| System Options | Full | Session/options only as required by application | Session/options only as required by application |
| Integrity Audit | Full | — | — |

## Governance decisions

1. Sales users no longer receive hard-delete permissions for Customers, Pipeline, Activities, Quotations, or Purchase Orders.
2. Sales Managers retain delete rights within their team scope.
3. Super Admin retains full administrative control.
4. Export permissions are explicit rather than falling back implicitly to `view`.
5. Existing data-scope enforcement remains in the routers; this change does not broaden a user's record visibility.
6. The existing human-readable role matrix remains backward compatible while the granular permission set becomes the canonical policy.

## Safety

This RBAC change is additive for read/create/edit/export paths and intentionally restrictive only for Sales hard-delete actions. It does not alter customer, opportunity, quotation, PO, target, or user records in the database.
