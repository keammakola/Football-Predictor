# Deployment

## Vercel container deployment

The root `Dockerfile.vercel` builds the React website with Node 22 and serves the
result through Nginx on port 80. Vercel detects that filename and deploys the
image as a container-backed Function. The root `vercel.json` selects the Container framework because the Dockerfile
owns the build.

1. Import `keammakola/Football-Predictor` into Vercel.
2. Use the repository root (`.`) as the Root Directory, not `frontend/`.
3. Use the **Container** framework preset. The container performs `npm ci` and
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

## Historical data deployment

The live website at https://betting.keabetswe.online serves fixed, verified
historical exports from `frontend/public/data/`. It has no live fixture section
and needs no API credentials, database, scheduled workflow or deployment hook
for data updates. Both research workflows are manual-only and disabled on GitHub.

The Python pipeline remains in the repository for reproducibility. To publish a
new historical experiment, rebuild and verify the backtest and its provenance
using the root README commands, then commit the matching exports and source
artifacts together. Pushing changes to `main` deploys the updated website.

## Static Vite alternative

If you prefer Vercel's static CDN deployment, create a Vercel project with Root
Directory `frontend/`, Framework Preset **Vite**, Build Command `npm run build`,
and Output Directory `dist`. With that root, the repository's container files
are outside the deployment root. The same committed JSON exports are served.

Reference: [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite).
