# Technical Debt & Deferred Work Log

## TransitPulse — NYC Subway Reliability Analytics Platform

**Purpose:** Record anything intentionally deferred, simplified, or left incomplete, at the moment the decision is made. This is a living document — entries are added in the same commit/PR as the decision they describe wherever possible, not reconstructed from memory afterward.

**How to use this log:** Every entry needs a reason. "We didn't have time" is a valid reason as long as it's stated — the goal isn't to justify every deferral extensively, it's to make sure nothing is silently forgotten. When an item is resolved, move it to the Resolved table at the bottom rather than deleting it, so the project's history stays visible.

---

## Active Items

| ID | Item | Category | Reason for deferring | Target | Date logged |
|---|---|---|---|---|---|
| TD-001 | Ingestion uses triggered/looped polling (~10-15 min trigger, looped within run) rather than a truly continuous ~30-second process | Known limitation (accepted trade-off) | Free-tier hosting landscape has no zero-maintenance always-on option (see ADR-001 in Architecture Document); prioritized maintainability and cost over literal continuous polling | Revisit only if a future requirement demands sub-minute latency guarantees — see ADR-001 Future Evolution section for the migration path | 2026-07-20 |

*(TD-002 and TD-003, previously logged here, were reclassified on 2026-07-21 — see Resolved Items below. They were validation tasks, not accepted engineering trade-offs, and are now tracked in `M0_RELEASE_CHECKLIST.md` instead.)*

*(No other items logged yet — implementation has not started. This log will be updated as M0 and subsequent milestones proceed.)*

---

## Resolved Items

| ID | Item | Category | Resolution | Resolved in |
|---|---|---|---|---|
| TD-002 | M0 code untested against live MTA feed / real Neon / real GitHub Actions execution | Reclassified — not tech debt | Determined to be a deployment validation task (closes automatically on first successful live run), not an accepted engineering trade-off. Moved to `M0_RELEASE_CHECKLIST.md` item "GitHub Actions workflow executes successfully" / "GTFS feed successfully ingested." | 2026-07-21 |
| TD-003 | `GTFS_FEED_URL` default unverified against live MTA endpoint | Reclassified — not tech debt | Same reasoning as TD-002 — a one-time verification step, not a standing compromise. Moved to `M0_RELEASE_CHECKLIST.md` item "GTFS feed successfully ingested." | 2026-07-21 |

---

## Category Reference

- **Deferred improvement** — a better approach was identified but not implemented now (e.g., "could use a more sophisticated anomaly-detection method")
- **Known limitation** — an accepted constraint of the current design (e.g., TD-001)
- **Future optimization idea** — a performance/cost/maintainability improvement not currently necessary but worth remembering (e.g., "could add database indexes once query patterns are known from real usage")
