# Deployment

## Vercel container deployment

The root `Dockerfile.vercel` builds the React website with Node 22 and serves the
result through Nginx on port 80. Vercel detects that filename and deploys the
image as a container-backed Function. The root `vercel.json` disables frontend
framework auto-detection because the Dockerfile owns the build.

1. Import `keammakola/Football-Predictor` into Vercel.
2. Use the repository root (`.`) as the Root Directory, not `frontend/`.
3. Keep the Framework Preset as **Other**. The container performs `npm ci` and
   `npm run build`; do not set a separate Vite output directory.
4. Keep the default HTTP port 80 and deploy.

No odds API key is needed for serving the website. Do not add private credentials
as `VITE_*` variables: Vite embeds those values in browser code.

The Dockerfile contains only the built website and committed public JSON data.
It does not run Streamlit, model training, or fixture refresh jobs on requests.
Container-backed Functions use Vercel's Function pricing and limits.

References: [Vercel container deployments](https://vercel.com/kb/guide/does-vercel-support-docker-deployments).

## Local Docker

```bash
docker compose up --build -d
```

Open http://localhost:8080. To stop the local website:

```bash
docker compose down
```

The generic `Dockerfile` and `Dockerfile.vercel` intentionally share the same
build and runtime configuration. Keep them in sync when changing the image.

## Updating predictions

Deployment serves a data snapshot. Generate fresh data with the Python pipeline,
commit changes to `frontend/public/data/`, and push them to the connected branch
so Vercel deploys the new snapshot. The build does not fetch odds or train models.
Use the root README for refresh commands. Upcoming matches still need fresh
snapshots as their scheduled dates approach.

## Static Vite alternative

If you prefer Vercel's static CDN deployment, create a Vercel project with Root
Directory `frontend/`, Framework Preset **Vite**, Build Command `npm run build`,
and Output Directory `dist`. With that root, the repository's container files
are outside the deployment root. The same committed JSON exports are served.

Reference: [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite).
