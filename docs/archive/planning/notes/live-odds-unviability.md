---
title: "Live Odds API Unviability"
date: "2026-10-04"
context: "Exploration of live data hooks for in-play automated betting."
---

# Live Odds API Unviability

We explored using free APIs to monitor live in-play odds for automated betting. We concluded this approach is unviable without significant financial investment.

DATA_Z3F9A1B7_START
- The Odds API free tier completely excludes soccer and restricts to 25 requests/day. [theoddsapi.com]
- API-Football allows free in-play odds tracking, but a strict 100 requests/day cap would deplete in minutes, making real-time monitoring impossible. [api-football.com]
- Sportmonks' free developer plan explicitly restricts all betting data (pre-match and in-play) to premium paid tiers. [sportmonks.com]
- Betfair Exchange API free developer tier only provides a "Delayed App Key"; true real-time data requires a funded, verified account and commercial keys. [developer.betfair.com]
DATA_Z3F9A1B7_END

**Decision:** We will focus strictly on pre-match predictions and automation.
