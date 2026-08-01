# M0 Release Checklist

## TransitPulse — Walking Skeleton

**Purpose:** This is the objective Definition of Done for M0. It supersedes the shorter checklist in `ROADMAP.md`'s M0 section (that one now points here) — this version exists so each item has a concrete verification method and a place to record evidence, not just a checkbox.

**Rule:** an item is only checked when there is real evidence to point to (a query result, a screenshot, a URL, a run ID) — not when it's believed to be working. This checklist is what future-you (or a future maintainer) uses to confirm M0 actually happened, not just that it was attempted.

---

| # | Item | Verification method | Status | Evidence | Date |
|---|---|---|---|---|---|
| 1 | Real Neon database provisioned and schema applied | `psql "$DATABASE_URL" -f src/db/schema.sql` succeeds against the real Neon project; `\dt` shows `raw_feed_event` and `ingestion_run_log` | ☐ Not started | | |
| 2 | GitHub Actions secrets configured | Repo Settings → Secrets and variables → Actions shows `DATABASE_URL` and `GTFS_FEED_URL` present (values not visible, presence is the check) | ☐ Not started | | |
| 3 | GitHub Actions workflow executes successfully | Manually trigger via `workflow_dispatch`; Actions tab shows a green run for `ingest.yml` | ☐ Not started | | |
| 4 | GTFS feed successfully ingested | The triggered run's logs show `fetch_feed()` returning data without an HTTP error, and `parse_feed()` returning a non-empty list | ☐ Not started | | |
| 5 | Data written to PostgreSQL | `SELECT count(*) FROM raw_feed_event;` returns > 0 after the run; `SELECT * FROM ingestion_run_log ORDER BY started_at DESC LIMIT 1;` shows `status = 'success'` | ☐ Not started | | |
| 6 | Two consecutive scheduled runs (not just manual) succeed | Actions tab shows two consecutive green scheduled (not `workflow_dispatch`) runs, confirming the cron schedule itself works unattended | ☐ Not started | | |
| 7 | Streamlit application deployed and runs correctly | App connected to Streamlit Community Cloud, reachable via public URL, shows non-zero record count and a recent `ingestion_run_log` row — not a connection error | ☐ Not started | | |
| 8 | Tests pass | `pytest` exits 0 locally, **and** the new `test.yml` CI workflow (added alongside this checklist — see below) shows a green run on the repo | ☐ Not started | | |
| 9 | Documentation updated to reflect real status | `README.md` M0 Definition of Done section reflects actual (not aspirational) status; `ROADMAP.md` M0 row updated to "Done"; this checklist fully filled in | ☐ Not started | | |
| 10 | M0 tagged and released | `git tag v0.1-m0` pushed; GitHub Release created for the tag, with release notes summarizing what M0 proves and linking this checklist as evidence | ☐ Not started | | |

---

## Note on item 6 (new — not in the original list)

I added this because none of the originally listed items actually verify the **schedule itself** works unattended — only that a manual trigger works. Given ADR-001's entire premise rests on GitHub Actions running reliably on a schedule, a single `workflow_dispatch` success doesn't confirm that; two consecutive unattended scheduled runs does. If you'd rather keep the checklist to exactly your original nine items, I'd suggest folding this verification into item 3 instead of dropping it — the unattended-schedule check is the part of item 3 that actually matters most for M0's purpose.

## Note on item 8 (CI workflow added)

Tests could only be verified locally before now — there was no CI enforcement of "tests pass," which is a real gap against the branch policy in `ROADMAP.md` Section 1.1 ("tests pass" is a merge precondition). I've added `.github/workflows/test.yml` (runs `pytest` on push and pull request) so this is actually enforced, not just self-reported. See that file for details.

---

## Sign-off

M0 is formally closed when all items above are checked with evidence recorded, and this section is filled in:

- **Closed by:**
- **Date:**
- **Tag:** `v0.1-m0`
- **Notes / deviations from plan:**
