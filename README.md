# TransitPulse

**NYC Subway Reliability Analytics Platform** — a live data pipeline and dashboard measuring on-time performance for the NYC Subway's numbered lines (1/2/3/4/5/6/S), built to demonstrate a production-shaped data engineering pattern (ingest → store → transform → serve) that generalizes to SLA/reliability monitoring in any operations-heavy domain.

**Current status: M0 — Walking Skeleton** (see `ROADMAP.md`). This milestone proves the full stack connects end to end for one line's worth of data. It intentionally does **not** yet compute real on-time/delay metrics — that's M1.

Full project documentation:
- [`PRD.md`](./PRD.md) — problem statement, requirements, scope
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — system design and Architecture Decision Records
- [`ROADMAP.md`](./ROADMAP.md) — milestone plan and vertical-slice methodology
- [`TECH_DEBT.md`](./TECH_DEBT.md) — known limitations and deferred work, logged as they're decided

## Data provenance

MTA does not provide historical real-time data — only current feed state at request time. This project's historical record is built entirely from its own continuous ingestion, starting from whenever the pipeline first ran successfully. See `ingestion_run_log` in the database, or the "Most recent ingestion run" panel on the dashboard, for the actual collection start.

## Architecture (M0 scope)

```
GitHub Actions (scheduled every 15 min)
  -> polls MTA GTFS-Realtime feed in a loop for ~10 min
  -> parses protobuf into raw_feed_event rows
  -> writes to Neon PostgreSQL
  -> logs run outcome to ingestion_run_log

Streamlit dashboard (Streamlit Community Cloud)
  -> reads directly from the same Neon database
  -> shows record counts and latest ingestion run status
```

Full design rationale, including why GitHub Actions was chosen over an always-on VM, is in `ARCHITECTURE.md` (ADR-001).

## Project structure

```
.
├── .github/workflows/ingest.yml   # scheduled ingestion workflow
├── src/
│   ├── config.py                   # loads .env locally; no-op in CI (see module docstring)
│   ├── ingestion/
│   │   ├── poll_feed.py           # fetch + parse one polling cycle
│   │   └── run_ingestion.py       # loop driver invoked by the workflow
│   ├── db/
│   │   ├── connection.py          # DATABASE_URL -> psycopg2 connection
│   │   ├── init_db.py             # applies schema.sql against DATABASE_URL (cross-platform)
│   │   └── schema.sql             # M0 schema (raw_feed_event, ingestion_run_log)
│   └── dashboard/
│       └── app.py                 # Streamlit app
├── tests/
│   └── test_parse_feed.py         # parsing tests (no live network dependency)
├── docker-compose.yml             # local Postgres for development
├── requirements.txt
├── .env.example
└── (PRD.md, ARCHITECTURE.md, ROADMAP.md, TECH_DEBT.md)
```

## Local setup

**1. Clone and install dependencies**
```bash
git clone <this-repo-url>
cd transitpulse
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

**2. Set up a database**

Either run Postgres locally for development:
```bash
docker compose up -d
```
...or use a real Neon project (required for the deployed/production path). Either way, apply the schema using the project's own init script (cross-platform, uses the same `DATABASE_URL`/`.env` resolution as the rest of the app):
```bash
python -m src.db.init_db
```
Alternatively, if you have `psql` installed:
```bash
psql "$DATABASE_URL" -f src/db/schema.sql
```
Both are safe to re-run — every statement in `schema.sql` uses `IF NOT EXISTS`.

**3. Configure environment variables**
```bash
cp .env.example .env
# then edit .env with your real DATABASE_URL
```
`.env` is loaded automatically (via `python-dotenv`, see `src/config.py`) by every entry point in this project — no manual export step needed. In GitHub Actions and other CI/deployment environments, this loading is a no-op (no `.env` file is present there) and real secrets set as environment variables are never overridden by it.

`GTFS_FEED_URL` in `.env.example` is MTA's documented numbered-line feed endpoint as of this project's last verification — **confirm it against [MTA's Developer Resources](https://www.mta.info/developers) before relying on it**, since this was not (and cannot be, from this project's development environment) verified against a live network call at generation time.

**4. Run a single ingestion cycle locally**
```bash
python -m src.ingestion.run_ingestion
```
(Running `python src/ingestion/run_ingestion.py` directly also works — both forms are supported.)

**5. Run the dashboard**
```bash
streamlit run src/dashboard/app.py
```

**6. Run tests**
```bash
pytest
```

## Deployment (production path)

1. **Database:** create a Neon project, apply `src/db/schema.sql` against it.
2. **Ingestion:** add `DATABASE_URL` and `GTFS_FEED_URL` as GitHub Actions repository secrets (Settings → Secrets and variables → Actions). The workflow in `.github/workflows/ingest.yml` runs automatically on its schedule once secrets are set, or can be triggered manually via the Actions tab (`workflow_dispatch`).
3. **Dashboard:** connect this repo to Streamlit Community Cloud, set `DATABASE_URL` in the app's secrets, and point it at `src/dashboard/app.py`.

## M0 Definition of Done

Per `ROADMAP.md`:
- [ ] Workflow runs on schedule without manual intervention (verify in the Actions tab after secrets are configured)
- [ ] Neon database contains real ingested rows from at least two consecutive scheduled runs
- [ ] Deployed dashboard is reachable via a public URL and shows live (not sample) data
- [ ] `pytest` passes in CI
- [ ] A fresh clone can be set up and run using only this README

These are checked off as they're verified against real infrastructure — the code in this repo satisfies the implementation side of each item, but live verification (a real Neon project, real GitHub secrets, a real Streamlit Cloud deployment) requires accounts this development environment doesn't have access to. See the note at the end of this document.

## A note on what's been verified vs. what hasn't

This codebase was written and syntax-checked (`py_compile` on every module, YAML-validated workflow) in an environment without network access, so nothing here has been run against the **live** MTA feed, a **real** Neon database, or an actual GitHub Actions run yet. That verification is the next concrete step: provision Neon, add the GitHub secrets, and trigger the workflow manually (`workflow_dispatch`) to confirm the walking skeleton actually walks. Please report back what happens — if the feed URL or parsing logic needs correction against real data, that's expected at this stage, not a sign of a design problem.
