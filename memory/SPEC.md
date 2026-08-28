# CRM Sales Management Production — Living Specification

## Product scope
Reference-compatible Indonesian industrial B2B CRM. The delivered first release mirrors the audited reference application's 11 authenticated modules: Dashboard, Customers, Sales Pipeline, Aktivitas/Tasks, Quotations, Purchase Orders, Order Monitoring, Sales Team, Audit Log, Users, Products, and Settings.

## Architecture
- React 19 + TypeScript + Tailwind v4 frontend, FastAPI service layer, MongoDB persistence.
- All browser requests use relative `/api` paths through the typed fetch boundary.
- Server-side pagination/search, indexed collections, server-side KPI/quotation calculations, CSV exports, PDF quotation output, and restricted local document uploads.
- Authentication uses a bcrypt password hash and an httpOnly same-origin session cookie. Roles: `SUPER_ADMIN`, `SALES_MANAGER`, `SALES`.

## Core data model
- Users own opportunities and activities; managers are connected by `manager_id`.
- Customers relate to contacts, opportunities, activities, quotations, and purchase orders by UUID string ids.
- Quotations and purchase orders contain validated line items referencing products.
- Purchase orders feed the six-stage delivery workflow: Received → Processing → Indent → Ready Stock → Delivery → Completed.
- Audit records capture login, create, update, delete, export, and status-change events.
- AI conversations and messages persist in MongoDB; the server supplies only role-visible selected CRM context to GPT-5.4 and audits generation plus confirmed-save actions.

## Key flows
1. Login with a seeded role, review real aggregated dashboard metrics, then logout.
2. Search/page customers, create validated customers with duplicate warnings, and delete records.
3. Create opportunities and review weighted pipeline in table or Kanban mode.
4. Record sales activities, review tasks, and mark tasks complete.
5. Create quotations with server-calculated totals and download PDF output.
6. Create customer purchase orders with optional restricted document upload, then advance delivery status in Order Monitoring.
7. Create products and users; inspect team KPIs, settings matrix, and audit history.
8. Open the GPT-5.4 CRM AI Copilot globally or from route-aware dashboard/customer/opportunity/quotation context, stream a response, and explicitly confirm before saving it as a linked CRM note.

## Seed facts
- 3 demo users, 50 customers, 50 opportunities, 100 activities, 50 tasks, 50 products, 30 quotations, and 20 purchase orders.
- Indonesian industries and cities; IDR is the primary currency.

## Intentional deviations
- Per the user's explicit choice, this pod keeps the template's FastAPI + MongoDB stack instead of migrating to Node.js + PostgreSQL.
- Navigation first matches the audited reference app. Extra modules from the wider master backlog (standalone Leads, Projects, Tenders, Targets, Calendar, and extended Reports) are not exposed as dead menu items in this release.