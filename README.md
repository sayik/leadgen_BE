# Leadgen Backend — Phase 1

Customer-centric CRM backend for a 15–50 employee business. Phase 1 focuses on the core customer workspace and manual interaction workflow. It intentionally does **not** yet implement telephony, WhatsApp delivery, push notifications, AI, or automatic cellular call-log capture.

## Included

- Organization bootstrap and JWT authentication
- Organization-scoped users and teams
- Customer profiles and multiple phone/email contacts
- Unified manual interactions: phone, WhatsApp, email, in-person, other
- Sales leads and service cases
- Tasks/reminders
- Team/employee transfers with history
- Audit events for key creation and transfer actions
- PostgreSQL, SQLAlchemy async, Alembic, Docker Compose
- OpenAPI docs at `/docs`

## Run locally

Requires Docker and Python 3.11+.

```bash
cp .env.example .env
# Change SECRET_KEY before using beyond local development.
docker compose up -d db
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Alternatively run the whole stack:

```bash
cp .env.example .env
docker compose up --build
```

The API expects the database schema to be migrated before use. For the Docker-only workflow, run:

```bash
docker compose exec api alembic upgrade head
```

## First organization / administrator

`POST /api/v1/auth/register-organization`

```json
{
  "organization_name": "Acme Ltd",
  "timezone": "Asia/Kolkata",
  "full_name": "Admin User",
  "email": "admin@example.com",
  "password": "ChangeThisPassword123!"
}
```

Then authenticate:

`POST /api/v1/auth/login` with form fields `username` (email) and `password`.

Use `Authorization: Bearer <access_token>` for subsequent requests.

## Main API areas

- `/auth`
- `/users`
- `/teams`
- `/customers`
- `/interactions`
- `/leads`
- `/cases`
- `/tasks`
- `/transfers`

All business records are organization-scoped from the authenticated user. Do not trust a client-supplied `organization_id`.

## Phase 1 interaction workflow

1. Create or locate a customer.
2. Add contact details as needed.
3. Record an interaction and choose its channel.
4. Optionally create a lead or service case.
5. Create a task/reminder with an owner and due time.
6. Transfer customer/lead/case responsibility using `/transfers`.

## Important implementation notes

- Phone numbers are normalized to E.164 when possible. The API currently expects a country region (defaults to `IN`) for national-format numbers.
- Customer profile fields are progressively enriched; fields are optional. Relationship ownership supports both a team and an individual employee.
- Customer relationship owner, lead owner and case owner are separate concepts.
- Transfers preserve a transfer history and do not duplicate customer records.
- Tasks are stored durably in PostgreSQL. A future worker can poll due tasks and send notifications.
- Passwords are hashed with Argon2.
- This is an initial development baseline, not a production-hardened deployment. Add rate limiting, email verification, refresh-token rotation, backups, observability, security review and integration-specific webhook verification before production.

## Version control

This project is initialized as a Git repository. See `git log` for the initial implementation commit.
