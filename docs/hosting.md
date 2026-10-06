# Hosting the historical website

The deployed website serves committed JSON; it needs no Python runtime, database,
odds key or cron job. Research runs and data publication happen separately.

## Local development

Use Node 22:

```bash
cd frontend
npm ci
npm run dev
```

Build with `npm run build` and preview with `npm run preview`.

## Docker

From the repository root:

```bash
docker compose up --build -d
```

Open http://localhost:8080. The multi-stage Dockerfile builds the Vite frontend
and serves it with Nginx. `/healthz` is the health endpoint. Static assets receive
immutable caching; JSON receives no-cache headers and missing data returns 404.
The SPA fallback handles frontend navigation.

`.dockerignore` limits build inputs to the website and server configuration.
Private environments and credentials are excluded. Do not mount local research
or credential directories into the published container.

## Vercel

The existing deployment uses the repository root, the Container framework and
`Dockerfile.vercel`, as declared in `vercel.json`. The custom domain is
https://betting.keabetswe.online. Manage domain records and project settings in
Vercel and the domain's DNS provider; do not put deployment tokens in the repo.

If using another static host, publish `frontend/dist` after the build and configure
SPA fallback with real 404 responses for missing data files.

## Updating historical evidence

Follow [snapshot instructions](snapshot.md). Validate before committing or
publishing, and review whether changing the data invalidates an article's figures.
CI validates the evidence but does not train or refresh it. Existing optional
GitHub data workflows have no schedule; they are unnecessary for this website.
