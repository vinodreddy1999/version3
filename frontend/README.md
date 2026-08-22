# Metam ERP — frontend

React 19 + TypeScript + Vite + TanStack Query + Tailwind CSS. No mock data —
every page reads and writes through the FastAPI backend in `../backend`.

## Getting started

```bash
npm install
cp .env.example .env   # set VITE_API_BASE_URL if the backend isn't on 127.0.0.1:8000
npm run dev
```

Requires the backend running (see `../backend/README.md` or the root
`README.md`) — sign in or create a new organization from the login page.

## Scripts

- `npm run dev` — start the Vite dev server
- `npm run build` — type-check (`tsc -b`) and produce a production build
- `npm run lint` — oxlint
- `npm run preview` — preview the production build locally

## Structure

- `src/api/` — typed API client functions (`endpoints.ts`) and response
  types (`types.ts`), one group per backend module
- `src/contexts/` — auth session and selected-plant state
- `src/components/` — shared layout and UI primitives
- `src/pages/` — one page per module (org, inventory, warehouse,
  production, procurement, sales, maintenance, quality) plus the
  dashboard and login pages
