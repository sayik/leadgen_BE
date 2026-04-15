# Leadgen — Project State and Development Handoff

> **Canonical project context.** Update this file whenever scope, architecture, implementation status, or a significant decision changes. At the start of a later development session, read this file and inspect the Git history and working tree before changing code.

## 1. Product summary

Leadgen is a client-centric lead and service relationship management system for businesses with approximately 15–50 employees. It serves both sales and service workflows.

The central record is the **customer**, not the individual call or lead. A customer profile is progressively enriched over time with contact details, company/context, interaction history, sales leads, service cases, ownership, and follow-up tasks.

The system must help the company:
- Retain a shared record of customer and prospect contact details.
- Capture what happened across phone, WhatsApp, email, and in-person interactions.
- Make ownership and handoff between employees/teams explicit.
- Schedule and complete follow-ups so opportunities and service obligations are not missed.
- Eventually identify new inbound numbers and trigger fast callback workflows.
- Eventually notify staff through in-app/web push and WhatsApp.

## 2. Product decisions already made

| Area | Decision |
|---|---|
| Calling setup | Mixed: normal cellular calls and business/VoIP calls |
| Team size | 15–50 employees |
| Business workflow | Both sales and service |
| Notifications | Both in-app/push and WhatsApp |
| Customer data model | Customer-centric, progressively enriched after first contact |
| Interaction channels | Phone, WhatsApp, email, in-person; extensible to other |
| Handoff | Clickable reassignment to another employee/team from the dashboard |
| Client app | Web dashboard designed to be usable as a mobile app/PWA; native app can be evaluated later |
| Automation | Manual interaction capture first; automate integrations later |

## 3. Phase 1 scope and implementation status

Phase 1 is the **manual CRM foundation**. It is not the automated telephony/notification phase.

### Implemented in the codebase (runtime verification still pending)

- Organization registration and first administrator creation.
- JWT bearer login and current-user endpoint.
- User roles: admin, manager, sales, service.
- Organization-scoped employee and team records.
- Team membership.
- Customer profiles with optional/enrichable fields.
- Multiple contact records per customer (phone/email/other).
- Phone normalization to E.164, with India (`IN`) as the default parsing region.
- Duplicate contact protection within an organization.
- Customer relationship owner (employee and team).
- Interaction records with channel and direction:
  - phone
  - WhatsApp
  - email
  - in-person
  - other
- Sales lead records and pipeline statuses.
- Service case records and statuses.
- Follow-up tasks with owner, due time, priority, and status.
- Reassignment/transfer of customer, lead, or case with transfer history.
- Initial audit events for selected create/transfer operations.
- Customer timeline endpoint.
- Dashboard summary endpoint.
- PostgreSQL, SQLAlchemy async, Alembic, Dockerfile and Docker Compose setup.
- Basic GitHub Actions CI workflow and starter tests.

### Explicitly not implemented in Phase 1

- Automatic capture of cellular call logs or caller ID from employee phones.
- Telephony/VoIP provider integration or call webhooks.
- Automatic detection/creation of a customer from an unknown inbound number.
- Immediate callback alert orchestration.
- WhatsApp Business Cloud API message delivery.
- WhatsApp notification templates, opt-in/consent management, delivery receipts.
- Web push/mobile push notification delivery.
- Background task scheduler/worker for due reminders.
- Email sending.
- Real-time dashboard updates/websockets.
- Native mobile application.
- AI summaries, lead scoring, or automated recommendations.
- Reporting/analytics beyond the initial summary endpoint.

These are future integration/automation capabilities. Do not describe them as working features until implemented and tested.

## 4. Current technical architecture

- **Language:** Python 3.11+ (Docker image currently uses Python 3.12)
- **API:** FastAPI
- **Persistence:** PostgreSQL 17
- **ORM:** SQLAlchemy 2.x async
- **Migrations:** Alembic
- **Validation/settings:** Pydantic v2 and pydantic-settings
- **Authentication:** JWT bearer tokens; Argon2 password hashing
- **Phone normalization:** `phonenumbers`
- **Containerization:** Docker / Docker Compose
- **API documentation:** FastAPI OpenAPI/Swagger at `/docs`
- **Frontend:** Not part of this backend repository yet; product direction is a responsive web dashboard/PWA.

### Code layout

```text
app/
  api/          HTTP routers and request handling
  core/         settings, database, security, dependencies
  modules/      SQLAlchemy domain models
  schemas.py    Pydantic request/response schemas
  main.py       FastAPI application and lifespan
migrations/
  env.py
  versions/     Alembic revisions
tests/
.github/workflows/
```

### Main domain entities

`Organization`, `User`, `Team`, `TeamMember`, `Customer`, `Contact`, `Interaction`, `Lead`, `ServiceCase`, `Task`, `Transfer`, `AuditLog`.

Important distinctions:
- Customer relationship owner, lead owner, and case owner are separate fields.
- A customer can have multiple contact details and multiple leads/cases/interactions/tasks.
- A task can be associated with a customer and optionally a lead or a case.
- An interaction is linked to a customer and optionally a lead or case.
- Transfers update the target entity's ownership and create a transfer-history record.

## 5. API surface currently present

All business routes are under `/api/v1`.

| Router | Prefix | Purpose |
|---|---|---|
| Authentication | `/auth` | Register organization, login, current user |
| Users | `/users` | List/create employees |
| Teams | `/teams` | List/create teams and add members |
| Customers | `/customers` | Customer CRUD, contacts, timeline |
| Interactions | `/interactions` | Record/list interactions |
| Leads | `/leads` | Sales pipeline CRUD |
| Cases | `/cases` | Service case CRUD |
| Tasks | `/tasks` | Follow-up/reminder CRUD |
| Transfers | `/transfers` | Reassign customer/lead/case and list history |
| Dashboard | `/dashboard/summary` | Initial KPI counts |

Health endpoint: `/health`.

The OpenAPI schema at `/openapi.json` is the detailed contract. Re-check it after API changes rather than relying only on this summary.

## 6. Important product/technical rules

1. **Tenant isolation:** derive `organization_id` from the authenticated user. Never accept a client-supplied organization ID as authority.
2. **Customer deduplication:** contact values are unique within an organization after normalization. A future inbound-call ingestion endpoint must resolve an existing contact before creating a new customer/contact and must handle races/duplicate webhook delivery.
3. **Unknown caller workflow (future):** create a durable inbound-call event, flag it as unknown/new, assign/escalate it, and create a callback task/notification. Do not rely on an ephemeral websocket event as the only record.
4. **Reminder reliability (future):** reminders must be stored durably, processed by a worker, retried safely, and made idempotent. The database task is the source of truth; WhatsApp/push are delivery channels, not the task record.
5. **Contact history:** preserve interaction channel, direction, timestamp, employee, summary/outcome, and next steps.
6. **Handoff:** transfer history must remain queryable. Reassignment should not create duplicate customer records.
7. **Timezone:** store timestamps as timezone-aware values (prefer UTC); display/schedule using the organization's configured timezone.
8. **Privacy/consent:** phone, WhatsApp and email contact data require appropriate access controls, retention policy, and consent/opt-out handling before outbound messaging.
9. **Mobile strategy:** keep the API client-independent and build responsive/PWA UI first. Native mobile features may be required later for call-log access; iOS and Android have different OS restrictions.
10. **Production readiness:** require security review, rate limiting, refresh-token strategy, password reset/email verification, backups, observability, and integration webhook verification before production.

## 7. Known validation gaps / cautions

- The repository has been scaffolded and versioned, but a complete PostgreSQL-backed integration test run has not yet been demonstrated.
- The current starter tests are not a substitute for endpoint-level integration tests.
- Review every API's tenant scoping and cross-entity relationship checks before production; add tests for cross-organization IDs and role permissions.
- Validate migration upgrade/downgrade against a fresh PostgreSQL database.
- Validate the Docker Compose path end-to-end, including migration execution.
- The current audit coverage is partial, not a complete immutable audit trail.
- Authentication currently issues access tokens; production refresh-token rotation, revocation, password reset and account recovery remain future work.
- Confirm task completion, overdue-task handling and concurrent updates with tests.
- Treat any unverified behavior as unverified; do not infer that code works merely because files exist.

## 8. Recommended next development sequence

### Phase 1 hardening (do before expanding scope)

1. Run migrations against a clean PostgreSQL database; verify schema and downgrade behavior.
2. Add API integration tests for auth, organization isolation, customer/contact deduplication, interactions, leads, cases, tasks and transfers.
3. Audit tenant isolation and authorization on every endpoint, including nested IDs.
4. Add pagination/filtering consistently and validate response schemas.
5. Verify phone normalization and duplicate handling, including concurrent requests.
6. Improve customer timeline shape and dashboard metrics based on frontend needs.
7. Publish/lock the OpenAPI contract for frontend integration.
8. Add CI service container for PostgreSQL-backed tests.

### Phase 2 candidate scope (confirm before implementation)

- Inbound call event ingestion and unknown-number detection.
- Telephony/VoIP integration adapter(s).
- Mobile/PWA notification registration and push delivery.
- Durable reminder scheduler/worker with retries and idempotency.
- WhatsApp Business Cloud API adapter, templates, opt-in, delivery status and failure handling.
- Notification preferences, escalation rules and team routing.
- Frontend dashboard integration and operational monitoring.

Phase 2 must be planned against the actual Phase 1 schema and API contract. Do not build an integration until its provider, event semantics, permissions, and failure/retry behavior are decided.

## 9. Development workflow and source-of-truth rules

At the beginning of each development session:

1. Read this file.
2. Run `git status --short --branch`.
3. Run `git log --oneline -10`.
4. Inspect the current code and migrations relevant to the requested change.
5. Treat the code and migrations as the implementation truth; this file is the product/architecture/status handoff.

At the end of each meaningful change:

1. Update this file if scope, status, architecture, API, decisions, or next steps changed.
2. Update `README.md` if setup or user-facing developer instructions changed.
3. Add/update tests and migrations with schema changes.
4. Run formatting, static checks, tests, and migration checks; record what actually passed.
5. Commit a focused Git change with a descriptive message.
6. Report the commit hash, changed files, tests run, and known gaps.

Do not silently rewrite history. Use new commits for ongoing work. Keep secrets and `.env` files out of Git.

## 10. Current repository checkpoint

- Repository: `leadgen-backend`
- Primary branch: `main`
- Latest checkpoint when this file was written: see `git log -1 --oneline`.
- Current phase: Phase 1 foundation; hardening/verification remains.
- Frontend repository: not yet linked/documented here.
- Remote Git hosting: not yet configured/confirmed.
- Last full PostgreSQL integration test result: not yet recorded.

Update this checkpoint after each development milestone. Git commit history is the authoritative implementation timeline; this document is the concise handoff and current-state summary.
