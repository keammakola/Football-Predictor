---
title: Tune Strong Tier Thresholds
date: 2026-10-04
priority: high
---

Focus the Elo and gradient boosting models on isolating matches with a 75%+ win probability. This tier (currently defined as "Strong" in `config.py`) should be heavily backtested and tuned to ensure it consistently identifies heavy favorites that actually win at that expected rate.
