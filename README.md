# Metam ERP (v3)

A ground-up rebuild of the Metam Services manufacturing ERP: a real,
database-backed multi-tenant FastAPI backend — no mock data anywhere — with a
React + TypeScript frontend that consumes it directly.

## Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, JWT auth (`python-jose`),
  `bcrypt` password hashing, Pydantic v2 settings.
- **Frontend**: React 19, TypeScript, Vite, TanStack Query, Tailwind CSS.
- **Database**: PostgreSQL in production; SQLite by default for local dev
  (set `DATABASE_URL` to switch).

## Architecture

Multi-tenant hierarchy: **Tenant → Company → Plant**, with RBAC (`Role` /
`Permission`) scoped per tenant. Every domain table is tenant-scoped, and
every write in one module that affects stock (receiving, shipping, picking,
production) posts through the same inventory ledger, so the numbers on the
dashboard are always derived from the same tables everything else writes to.

### Modules

| Module | What it does |
|---|---|
| Org | Companies and plants under each tenant |
| Inventory | Items, stock balances, and a movement ledger (receipt/issue/adjustment/transfer) |
| Warehouse | Warehouses → zones → bins, bin-level stock, putaway and pick tasks |
| Production | Bills of material, production orders that consume components and produce finished goods |
| Procurement | Suppliers and purchase orders (draft → submit → receive, partial receipts supported) |
| Sales | Customers and sales orders (draft → confirm → ship, partial shipments supported) |
| Maintenance | Assets and maintenance work orders (open → start → complete/cancel), asset status tracks active work |
| Quality | Inspections with inline defect recording and a resolution workflow |
| Reports | A dashboard endpoint aggregating live numbers across every module above |

## Running locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # JWT_SECRET should be set for anything beyond local dev
alembic upgrade head
uvicorn app.main:app --reload
pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # point VITE_API_BASE_URL at the backend if not on 127.0.0.1:8000
npm run dev
```

Open the frontend, create a new organization from the login page, and start
using the app — every action goes through the real backend.

## Running with Docker

```bash
cp .env.example .env   # set POSTGRES_PASSWORD and JWT_SECRET
docker compose up --build
```

This starts Postgres, the backend (migrations run automatically on
container start — see the caveat in `backend/Dockerfile` for multi-replica
deployments), and the frontend served by nginx on port 8080. **Port 8080 is
the only thing you need to expose publicly** — nginx serves the built
frontend and reverse-proxies `/api/*` to the backend on the private compose
network (see `frontend/nginx.conf`), so the app is same-origin (no CORS to
configure) and works from any host or domain without rebuilding the image.
The backend container itself is not published to the host.

For a real (non-localhost) deployment, also set `FRONTEND_BASE_URL` in
`.env` to the actual public URL people will use — it's baked into
password-reset email links.

## Security notes

- JWT secret is read from `JWT_SECRET`; if unset, a random per-process
  secret is generated (dev convenience only — never rely on this in a
  shared/deployed environment).
- Passwords are hashed with `bcrypt` directly (72-byte input cap enforced
  explicitly, matching bcrypt's own limit).
- All domain queries are scoped by `tenant_id` — see the ownership-check
  helpers in each `app/api/routes/*.py` module and the RBAC dependency in
  `app/api/deps.py`.
- Both application containers run as non-root users with health checks;
  `/ready` verifies real database connectivity (not just process liveness),
  so an orchestrator won't route traffic to an instance that can't reach
  its DB. CI runs CodeQL and Dependabot keeps dependencies current.
- The backend trusts `X-Forwarded-*` headers from any peer
  (`--forwarded-allow-ips=*`) so the rate limiter keys on the real client
  IP instead of nginx's — safe only because the backend container is never
  published to the host, so nginx is the only thing that can reach it.
  Don't publish the backend's port without reconsidering this.

## CI

`.github/workflows/ci.yml` runs on every push and pull request: the backend
test suite, an Alembic migration check (applies cleanly from scratch),
frontend lint + build, both Docker images building, and the full Playwright
e2e suite against a real backend + frontend.
