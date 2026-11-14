# BuildGuard AI frontend

The frontend is a Next.js application. For setup and the full local run flow,
see the [root README](../README.md).

## Development

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_URL` in `.env.local` to the
FastAPI origin (default `http://localhost:8000`) and restart the dev server if
the backend uses another host or port.

## Checks

```powershell
npm run lint
npm run build
```

The upload page requires a running backend, a signed-in user, and an existing
project. Analysis additionally requires the trained checkpoint described in
the root README; without it the API rejects the analysis instead of showing
sample results.
