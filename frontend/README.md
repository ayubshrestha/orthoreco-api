# Orthoreco Frontend

React + Vite + TypeScript clinician/admin dashboard for the Orthoreco API.

## Stack

- React 19 + TypeScript
- Vite (dev server + build)
- React Router (client-side routing)
- Axios (HTTP)
- Recharts (graphs)

## Pages

- `/login` — sign-in for admin/clinician
- `/` — overview KPIs, recovery-bucket pie, surgery-type bars, top risk patients
- `/patients` — searchable/filterable table of all patients
- `/patients/:patientId` — single-patient detail with line charts (steps/active min, walking quality, recovery score) and full check-in history

## Setup

```bash
cd frontend
npm install
cp .env.example .env       # adjust VITE_API_URL if API not on default
npm run dev                # http://localhost:5173
```

The API must be running and reachable at `VITE_API_URL` (default `http://127.0.0.1:8000`). The backend's CORS middleware accepts `http://localhost:5173` and `http://127.0.0.1:5173` out of the box; override with the `CORS_ORIGINS` env var on the API side.

## Demo accounts

Seed via `python seed_demo_users.py` from the project root:

| Role | Email | Password |
|---|---|---|
| admin | `admin@demo.com` | `admin123` |
| clinician | `doctor@demo.com` | `doctor123` |

## Build

```bash
npm run build              # outputs to dist/
npm run preview            # serve the build
```
