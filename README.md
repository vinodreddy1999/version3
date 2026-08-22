# Metam ERP (v3)

A ground-up rebuild of the Metam Services manufacturing ERP: multi-tenant
FastAPI backend backed by a real relational database (no mock data), with a
React + TypeScript frontend.

## Status

Actively under construction. See commit history for progress; modules are
being built and pushed incrementally.

## Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, JWT auth (`python-jose`),
  `bcrypt` password hashing, Pydantic v2 settings.
- **Frontend**: React 19, TypeScript, Vite, TanStack Query, Tailwind CSS.
- **Database**: PostgreSQL in production; SQLite by default for local dev
  (set `DATABASE_URL` to switch).

## Architecture

Multi-tenant hierarchy: **Tenant → Company → Plant**, with RBAC (`Role` /
`Permission`) scoped per tenant. Every domain table is tenant-scoped.

## Backend: getting started

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit as needed; JWT_SECRET should be set for anything beyond local dev
alembic upgrade head
uvicorn app.main:app --reload
pytest
```

## Security notes

- JWT secret is read from `JWT_SECRET`; if unset, a random per-process
  secret is generated (dev convenience only — never rely on this in a
  shared/deployed environment).
- Passwords are hashed with `bcrypt` directly (72-byte input cap enforced
  explicitly, matching bcrypt's own limit).
- All domain queries are scoped by `tenant_id` — see RBAC dependency in
  `app/api/deps.py`.
