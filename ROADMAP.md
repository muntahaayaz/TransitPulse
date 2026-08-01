# Implementation Roadmap

## TransitPulse — NYC Subway Reliability Analytics Platform

| Field | Value |
|---|---|
| Document status | Draft v1.0 — pending approval |
| Last updated | 2026-07-20 |
| Depends on | PRD v1.1 (baseline) — Architecture v1.0 (baseline) |
| Tracking | This document is the narrative roadmap. Day-to-day task tracking uses GitHub Issues, tagged to the GitHub Milestone matching each milestone below. |
| Related process docs | `TECH_DEBT.md` (deferred work log) — Git workflow defined in Section 1.1 below |

**Purpose of this document:** This is the build methodology and milestone plan for implementation. It translates the PRD's requirements and the Architecture's component design into an ordered sequence of small, end-to-end deliverables, rather than a layer-by-layer build. It will be updated after each milestone closes to reflect actual status — this is a living document, not a one-time plan.

---

## 1. Methodology: Vertical Slices

Implementation proceeds in **milestones**, not layers. A layer-by-layer build (e.g., "finish all ingestion, then all schema, then all SQL, then the dashboard") would leave the project in a non-runnable state for most of its duration — risky for a solo, time-boxed effort, and a poor way to catch integration problems early.

Instead, **every milestone cuts through the full stack**: it touches ingestion, storage/schema, SQL transformation, dashboard, tests, and documentation together, and produces something small but real that runs end to end. This has three concrete benefits for this project specifically:

1. **The application is demonstrable at every milestone**, not just at the end — important given the continuous-collection strategy (ADR-001), since the ingestion pipeline needs to be live as early as possible to maximize the historical window.
2. **Integration risk is caught early.** If GTFS-RT parsing, Neon connectivity, or Streamlit Cloud deployment has a problem, we find out in Milestone 0, not in week 5.
3. **Each milestone is independently a legitimate commit checkpoint** — useful both for tracking real progress and for the GitHub history itself to read as a coherent engineering narrative rather than one large commit.

**Rule for every milestone:** if a milestone's scope can't be described as "a user-visible dashboard change backed by real, live-ingested data," it's not a valid vertical slice — it's infrastructure work that should be folded into the milestone that actually needs it.

---

## 1.1 Git Workflow & Branch Policy

`main` must remain in a working, deployable state at all times. It represents the current, demonstrable state of the project — not a staging area for incomplete work.

**Rule:** any change large enough to span multiple commits is developed on a feature branch and merged into `main` only when all of the following are true:
1. Tests pass
2. Documentation affected by the change is updated in the same merge (not deferred)
3. The application still runs end-to-end after the change (per each milestone's Definition of Done)

Small, self-contained fixes (e.g., a typo, a one-line config correction) may be committed directly to `main` at the author's judgment, since routing every trivial change through a branch would add process overhead without improving safety. Anything touching ingestion logic, schema, transformation SQL, or the dashboard goes through a branch.

**Why this matters for this project specifically:** the continuous ingestion pipeline (ADR-001) is expected to be running against `main`-deployed infrastructure for weeks at a time. A broken `main` doesn't just block development — it silently breaks historical data collection, which cannot be recovered retroactively. Keeping `main` stable is a data-integrity control here, not just a hygiene preference.

## 1.2 Technical Debt Log

Deferred work, known limitations, and intentional shortcuts are recorded immediately in `TECH_DEBT.md` at the moment the decision is made — not reconstructed from memory later. This applies to anything knowingly left incomplete, simplified, or postponed, regardless of how small it seems at the time. See `TECH_DEBT.md` for the current log; it is a living document, updated in the same commit/PR as the deferral it describes wherever possible.

---

## 2. Milestone Plan

Status legend: Not Started / In Progress / Blocked / Done. All milestones currently **Not Started** — this table will be updated as work proceeds.

| Milestone | Goal | Status |
|---|---|---|
| M0 — Walking Skeleton | Prove the full stack connects, end to end, for one line | Not Started |
| M1 — Core Reliability Metric | Real on-time/delay classification, full line subset | Not Started |
| M2 — Line & Station Breakdown | Where and when delays concentrate | Not Started |
| M3 — Trend & Historical View | Reliability over time, honest data-provenance disclosure | Not Started |
| M4 — Anomaly Signal (stretch) | Flag unusual delay spikes; prove line-expandability | Not Started |
| M5 — Hardening & Release | Full AC verification, polish, tagged v1.0 release | Not Started |

---

### M0 — Walking Skeleton

**Goal:** Prove every architectural component works together, at minimal scope, deployed live.

**Vertical slice includes:**
- Ingestion: GitHub Actions workflow polling the GTFS-RT feed for a single line (the "1" train) and writing raw records to Neon
- Database: minimal schema — one raw fact table, no dimensions yet
- SQL: a trivial query (e.g., row count / most recent observed positions) — not the real metric yet
- Dashboard: single-page Streamlit app, deployed to Streamlit Community Cloud, showing that trivial query's output using live data
- Tests: one automated test confirming a valid feed payload is correctly parsed and written
- Docs: README stub with setup instructions sufficient to reproduce this slice

**Explicitly NOT in this milestone:** on-time/delay logic, dimension tables, multi-line support, anomaly detection.

**Definition of Done:** see `M0_RELEASE_CHECKLIST.md` for the authoritative, evidence-based checklist (10 items, each with a verification method). The list below is kept only as a quick-reference summary — if the two ever disagree, the checklist file wins.
- [ ] Workflow runs on schedule without manual intervention and appears in GitHub Actions history
- [ ] Neon database contains real ingested rows from at least two consecutive scheduled runs
- [ ] Deployed Streamlit dashboard is reachable via a public URL and displays live data (not hardcoded/sample data)
- [ ] Automated tests pass locally and in CI (`test.yml`)
- [ ] README allows a fresh clone to be set up and run by following only the written steps (NFR-4 check)

**GitHub milestone marker:** tag `v0.1-m0`, GitHub Milestone "M0 — Walking Skeleton" closed, roadmap table above updated to Done.

---

### M1 — Core Reliability Metric

**Goal:** Real on-time/delay classification, across the full MVP line subset.

**Maps to:** FR-1 (revised), FR-2, FR-3, FR-4, FR-6 (partial — overall performance, no date-range selector yet), FR-10, NFR-1 (revised), NFR-2. AC-1, AC-2, AC-3, AC-4, AC-7.

**Vertical slice includes:**
- Ingestion: expanded to all seven in-scope lines (1/2/3/4/5/6/7)
- Database: dimension tables populated from static GTFS (routes, stops, trips, calendar); `ingestion_run_log` table implemented
- SQL: real on-time/delayed classification logic (FR-4), joined against dimensions
- Dashboard: overall on-time performance view (FR-6) using the real metric
- Tests: metric correctness verified against a manually spot-checked sample (AC-4); malformed-payload handling test (NFR-2)
- Docs: PRD/Architecture cross-references updated if implementation surfaced any correction to either document

**Definition of Done:**
- [ ] All seven lines ingesting successfully with dimension data correctly resolved
- [ ] On-time/delayed classification matches manual verification on a spot-checked sample
- [ ] A deliberately induced ingestion failure produces a reviewable log entry (AC-7)
- [ ] Dashboard's overall performance figure is traceable back to a specific SQL query a reader can inspect
- [ ] Tests pass in CI; test coverage includes both the happy path and at least one malformed-data case

**GitHub milestone marker:** tag `v0.2-m1`, Milestone closed, roadmap updated.

---

### M2 — Line & Station Breakdown

**Goal:** Answer *where* and *when* delays concentrate.

**Maps to:** FR-5, FR-7, FR-8. AC-5, AC-6 (partial).

**Vertical slice includes:**
- Ingestion: no change (already covers full subset)
- Database: no structural change expected — this milestone tests FR-13's structural intent (expand analysis, not schema) even before FR-13 itself is targeted
- SQL: aggregation by line, station, and time-of-day window (FR-5)
- Dashboard: by-line breakdown view (FR-7); station/time-window concentration view (FR-8)
- Tests: aggregation query correctness against known subsets of collected data
- Docs: updated screenshots/description in README reflecting new dashboard views

**Definition of Done:**
- [ ] Dashboard shows per-line on-time performance, matching independently spot-checked SQL output
- [ ] Dashboard shows at least one clear view of delay concentration by station and by time window
- [ ] New aggregation queries covered by tests
- [ ] README updated to describe the new views

**GitHub milestone marker:** tag `v0.3-m2`, Milestone closed, roadmap updated.

---

### M3 — Trend & Historical View

**Goal:** Show reliability over time, and disclose data provenance honestly.

**Maps to:** FR-9, FR-11. AC-6 (complete), AC-8.

**Vertical slice includes:**
- Ingestion: no change (should now have several weeks of accumulated history, per the collection window running in parallel since M0)
- Database: no structural change expected
- SQL: trend aggregation over the collection period
- Dashboard: trend view (FR-9); explicit provenance note stating the data collection start date and clarifying that history reflects only the collection window, not an agency-provided archive (FR-11)
- Tests: trend query correctness over a known date range
- Docs: README and dashboard both carry the provenance disclosure (AC-8)

**Definition of Done:**
- [ ] Trend view reflects genuine week-over-week (or finer) change using real accumulated data
- [ ] Provenance disclosure is visible in both the README and the dashboard itself, not just one
- [ ] All "Must"-priority functional requirements (FR-1 through FR-11, per PRD Section 5) are now satisfied
- [ ] Full AC-1 through AC-8 verification pass (PRD Section 13)

**GitHub milestone marker:** tag `v0.4-m3`, Milestone closed, roadmap updated. **This is the point at which the MVP's "Must" scope is functionally complete** — M4 is stretch, M5 is hardening.

---

### M4 — Anomaly Signal (stretch)

**Goal:** Flag unusual delay spikes; demonstrate the schema supports adding lines without redesign.

**Maps to:** FR-12 (Should), FR-13 (Should). AC-9, AC-10.

**Vertical slice includes:**
- Ingestion: no structural change
- Database: no schema change required — this milestone's success criterion for FR-13 *is* the absence of a required schema change
- SQL: simple statistical anomaly flag (method choice deferred to this milestone, per Architecture Section 7)
- Dashboard: anomaly indicator surfaced on an existing view (not necessarily a new page)
- Tests: anomaly logic tested against both a known-anomalous and known-normal synthetic case
- Docs: brief method explanation in README/Architecture addendum

**Definition of Done:**
- [ ] A real or deliberately introduced delay spike is visibly flagged (AC-9)
- [ ] An additional line can be added via configuration alone, with no schema migration (AC-10) — demonstrated, not just asserted
- [ ] Anomaly logic covered by tests

**Note:** If time-constrained, this milestone may be descoped to v1.1 per PRD Section 12 without affecting MVP completion — M3 already represents a complete, demonstrable MVP.

**GitHub milestone marker:** tag `v0.5-m4` (or explicitly skipped, documented as such), roadmap updated either way.

---

### M5 — Hardening & Release

**Goal:** Full acceptance verification, documentation completeness, tagged release.

**Maps to:** All remaining AC items (PRD Section 13); all NFRs (Architecture Section 6).

**Vertical slice includes:**
- Full walkthrough of every AC-1 through AC-12 with evidence recorded (not just asserted)
- README finalized: setup instructions, live dashboard link, provenance note, architecture summary, screenshots
- PRD and Architecture Document reviewed for any drift between what was planned and what was actually built, with corrections made rather than left inconsistent
- Test suite reviewed for coverage gaps
- GitHub Release published with release notes summarizing the build

**Definition of Done:**
- [ ] Every "Must"-priority AC item verified with recorded evidence
- [ ] README is sufficient for an unfamiliar engineer to understand and run the project without asking the original author
- [ ] PRD, Architecture Document, and README are mutually consistent (no contradictions between planned and as-built)
- [ ] Tagged GitHub Release (`v1.0`) published with descriptive release notes

**GitHub milestone marker:** tag `v1.0`, Milestone closed, roadmap updated to reflect final state, PRD/Architecture status fields updated to note implementation completion.

---

## 3. Traceability Summary

| Requirement | Delivered in |
|---|---|
| FR-1 (revised), FR-2, FR-3, FR-10, NFR-1 (revised), NFR-2 | M0 (skeleton), hardened in M1 |
| FR-4 | M1 |
| FR-6 | M1 (overall figure), refined through M3 (date-range/trend) |
| FR-5, FR-7, FR-8 | M2 |
| FR-9, FR-11 | M3 |
| FR-12, FR-13 | M4 (stretch) |
| All NFRs, all AC items | Verified cumulatively, confirmed in M5 |

This table exists so that "is requirement X done" always has a single, checkable answer rather than requiring a re-read of the whole roadmap.

---

## 4. Change Log

This section will be updated at the close of each milestone with actual outcomes, deviations from plan, and any requirement corrections discovered during implementation — consistent with the project's standard of documenting decisions rather than leaving them implicit.

| Date | Change |
|---|---|
| 2026-07-20 | Initial roadmap approved, no milestones started |
| 2026-07-22 | M0 bug found during live validation: `db/connection.py` never loaded `.env`, so `DATABASE_URL` was always missing locally despite README instructions. Fixed via a dedicated `src/config.py` (python-dotenv, `override=False`, no-op in CI). Not logged in `TECH_DEBT.md` — this was a defect with a direct fix, not an accepted long-term trade-off. |
| 2026-07-23 | M0 bug found during live validation: internal imports (`from config import`, `from db.connection import`, etc.) only worked when a specific script was run directly, because each entry point independently added `src/` (not the project root) to `sys.path`. This broke `-m` execution and `from src.x import y`-style imports, including `from src.db.connection import get_connection`. Fixed by standardizing on absolute imports rooted at the `src` package everywhere, and having entry points add the project root to `sys.path` instead of `src` itself. The first fix's verification (2026-07-22) only exercised the direct-script invocation path, which is why this wasn't caught at the same time — noted here rather than left unexplained. Also added `src/db/init_db.py` as a cross-platform way to apply `schema.sql`, reusing the same `DATABASE_URL` resolution path as the rest of the app. |
