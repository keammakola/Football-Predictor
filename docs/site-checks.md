# Website verification — 6 October 2026

The historical site uses the existing 925-bet export. Filters affect ledger rows;
headline statistics continue to describe the full experiment.

## Changes

- League and season filters combine with match search; space-separated search
  terms all need to match the fixture name.
- Changing filters resets the ledger to 50 rows and closes expanded details.
- Empty search results have a clear message and a reset control.
- Match details open with Enter or Space. Tables can receive keyboard focus for
  horizontal scrolling. Navigation includes active-state labels and a skip link.
- Muted and loss text use darker colours to pass the tested contrast checks;
  reduced-motion preferences disable animations and transitions.
- Tailwind 4 uses the official Vite plugin. Legacy PostCSS integration and its
  affected dependencies were removed. The design tokens remain in the existing
  Tailwind configuration.
- Overview and footer claims describe this historical experiment; the final
  season is partial. The article link remains unchanged.

## Completed checks

- Frontend lint and production build.
- `npm audit`: zero reported vulnerabilities in the frontend dependency tree.
- Real Chrome interaction checks: 50 → 100 → 925 rows → 50; combined league,
  season and team search compared against source JSON; no-results state; clearing
  filters; keyboard opening and closing of match details.
- Overview and Behind the Model at 320, 375, 768 and 1280 pixels: no page-wide
  horizontal overflow. Wide data tables scroll within their labelled regions.
- axe scans for WCAG 2 A/AA and WCAG 2.1 AA: zero detected violations on both
  pages at each tested width. Automated scans do not establish full accessibility
  conformance or replace testing with assistive technology.
- Mobile screenshots visually reviewed after the Tailwind migration.

The browser tools were installed temporarily in `/tmp/football-browser-checks`;
they are not shipped in the production container.
