# Football Predictor

## What This Is
A free, locally run model that predicts home win / draw / away win probabilities for Premier League matches and flags the matches it feels strongly about.

## Why It Matters
The ultimate goal is to maximize absolute hit rate (accuracy) rather than finding mathematically profitable (+EV) bets against closing lines. The architecture should prioritize reliably identifying high-probability winners (heavy favorites).

## Context & Constraints
- Cost: Completely free (free data, free tools, own machine)
- Scope: Premier League only, one model family at a time
- Injury/availability data: Free API route via daily snapshots

## Core Value
High hit rate on heavy favorites over mathematical market edge.

## Requirements

### Active
- [ ] REQ-001: Maximize Hit Rate Over Market Edge
- [ ] Implement Dixon-Coles model
- [ ] Integrate xG-based form features
- [ ] Tune Strong Tier Thresholds (isolate 75%+ win probability)

### Out of Scope
- [ ] Beating the bookmaker closing odds long-term (+EV) — Deprioritized in favor of hit rate.
- [ ] UI Polish — Streamlit UI is delayed until a high hit rate edge is established.

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Focus on hit rate | User wants a high frequency of winning bets | Pending |

---
*Last updated: 2026-10-04 after initialization*
