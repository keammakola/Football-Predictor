
### REQ-001: Maximize Hit Rate Over Market Edge
**Date:** 2026-10-04
**Description:** The primary goal of the model is to maximize the absolute hit rate (accuracy) rather than finding mathematically profitable (+EV) bets against closing lines. The architecture should prioritize reliably identifying high-probability winners (heavy favorites), even if payouts are small.


### REQ-002: Focus on Pre-Match Automation
**Date:** 2026-10-04
**Description:** The automated data hook system must strictly focus on fetching pre-match data and generating predictions prior to kickoff. In-play (live) odds tracking is explicitly out of scope due to the extreme rate limits and latency of free API tiers.
