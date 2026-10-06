# The Football Experiment website

React and TypeScript frontend for the historical evidence and simulated betting results.
This is the active website; older prototypes are archived under `docs/archive/`.

```bash
npm ci
npm run dev
npm run build
npm run lint
```

`src/App.tsx` contains the shared header, navigation, and footer. `MainPage.tsx`
shows the overview and ledger; `TechnicalPage.tsx` and `ProofOfWork.tsx` show
Behind the Model. Shared styles are in `src/index.css` and `tailwind.config.js`.

The frontend reads generated JSON snapshots from `public/data/`. Use `publish_snapshot.py` from the repository root to update the complete
validated bundle; see the root README and `docs/snapshot.md`. Do not edit data
files individually.
API credentials belong in the Python environment or ignored local config, never
in frontend code or public exports.
