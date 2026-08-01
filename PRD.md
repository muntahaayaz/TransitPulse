# Product Requirements Document

## TransitPulse — NYC Subway Reliability Analytics Platform

| Field | Value |
|---|---|
| Document status | **Approved v1.0 — baseline** |
| Author | [Your name] |
| Last updated | 2026-07-20 |
| Approved | 2026-07-20 |
| Document owner | Project lead (single-contributor project) |
| Related documents | Research Summary (prior phase, this conversation) — Architecture Document (in progress) — UX Plan (not yet written) |

**Approval note:** MVP line scope (Section 11: numbered lines 1/2/3/4/5/6/7) and Assumptions/Risks (Sections 8–9) reviewed and confirmed with no additional prior-experience findings to incorporate. Assumptions and risks stand as written and will be validated during implementation; this document will be updated if implementation reveals they were incorrect, per the traceability standard for this project.

**Revision note (v1.1, during Architecture phase):** FR-1 and NFR-1 were revised following a documented Architecture Decision Record (ADR-001, in the Architecture Document) comparing ingestion deployment platforms. The original wording specified continuous ~30-second polling; the approved architecture uses a triggered/looped polling pattern on GitHub Actions instead. This was an explicit, evaluated trade-off — not scope drift — see ADR-001 for the full comparison and rationale.

**Maintenance note for future readers:** This document is the single source of truth for *what* the product must do and *why*. It intentionally excludes *how* it will be built — implementation details, schema design, and infrastructure choices belong in the Architecture Document, which will reference this PRD's requirement IDs directly. If you are picking up this project and something here seems ambiguous, that is a defect in this document — open an issue rather than guessing.

---

## 1. Problem Statement

Transit riders and operators need a reliable way to answer a simple question that is surprisingly hard to answer from raw operational data: **is the system meeting its schedule, and where does it fail?**

Raw GTFS-Realtime feeds provide a continuous stream of vehicle positions and trip updates, but this data is not directly usable for decision-making. It is not stored historically by the transit agency, it is not aggregated into performance metrics, and it requires specialized parsing (protocol buffers) to access at all. As a result, the question "how reliable is this line, this station, this time of day?" cannot currently be answered without building infrastructure to capture, store, and analyze the feed over time.

This project builds that infrastructure: a data pipeline and analytics dashboard that ingests live NYC Subway GTFS-Realtime data, stores it durably, computes reliability metrics, and presents them in a form that supports operational decision-making.

**Why this problem, and why now:** This problem class — *is the system meeting its service-level commitment, and where does it break down* — is not specific to transit. It is structurally identical to SLA monitoring in logistics, uptime monitoring in infrastructure, and on-time-delivery tracking in e-commerce fulfillment. Transit is the domain instance chosen for this project because it offers a freely accessible, well-documented, real-time data source (see Research Summary, Section 2) that lets us build the full pattern end to end without paid data access.

---

## 2. Stakeholders

| Stakeholder | Role in this project | What they need from the product |
|---|---|---|
| Transit operations manager *(represented persona)* | Primary intended end user of the dashboard | Identify which lines/stations need operational attention, ranked by impact |
| City planning / policy analyst *(represented persona)* | Secondary intended end user | Trend data over time to support scheduling or investment decisions |
| Customer experience analyst *(represented persona)* | Secondary intended end user | Understand which rider segments (by line, by time window) are most affected by unreliability |
| Project owner (you) | Builder, maintainer, decision-maker | A working system that is technically defensible and clearly documented |
| Future maintainer (hypothetical) | Anyone who picks up this repository later | Documentation sufficient to understand and extend the system without the original author present |
| Portfolio reviewer (hiring manager) | Not a system user, but a critical audience for this document | Evidence of product thinking, not just code — this PRD itself is a deliverable they may read |

**Note on stakeholder representation:** Because this is a single-contributor portfolio project rather than a commissioned product, the "stakeholders" above are represented personas rather than interviewed users. This is documented explicitly rather than presented as if real stakeholder interviews occurred, because a false claim of user research would undermine the credibility of the entire document. Where requirements below reference stakeholder needs, they are grounded in publicly documented transit-industry KPIs (e.g., on-time performance, headway adherence) rather than direct interviews.

---

## 3. Business Objectives

| ID | Objective | How it's measured |
|---|---|---|
| BO-1 | Demonstrate a working, defensible answer to "is this system reliable, and where does it fail" | Dashboard correctly surfaces on-time performance by line, station, and time window |
| BO-2 | Prove the underlying data engineering pattern (ingest → store → transform → serve) generalizes beyond finance | Architecture and documentation explicitly describe the transferable pattern (see Section 1) |
| BO-3 | Produce a portfolio artifact that is comprehensible to Data Analyst, Business Analyst, Analytics Engineer, and Data Engineer reviewers within a short review window | External review/feedback confirms the README and dashboard communicate the business framing without requiring domain explanation |

These are the objectives for *this project as a portfolio artifact*. They are distinct from, but should not contradict, the product-level success metrics in Section 10.

---

## 4. Goals and Non-Goals

**Goals (v1):**
- Ingest live NYC Subway GTFS-Realtime data continuously and reliably
- Store ingested data durably in a properly modeled relational schema
- Compute on-time performance and delay metrics from stored data
- Present those metrics through an interactive dashboard
- Document the system to professional engineering standards

**Non-goals (v1):** explicitly *not* attempting in this version:
- Predicting future delays (forecasting/ML) — candidate for a future, separate project
- Covering the full subway system (all 26 lines) — v1 covers a defined subset (see Section 11)
- Covering buses, LIRR, or Metro-North — subway only
- Real-time alerting/notifications to end users
- Multi-user authentication or access control — this is a single-operator analytics tool, not a multi-tenant product

---

## 5. Functional Requirements

Each requirement has a stable ID for traceability into the Architecture Document, test plan, and acceptance criteria (Section 13).

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | *(Revised — see ADR-001 in Architecture Document)* The system shall ingest MTA GTFS-Realtime Trip Update and Vehicle Position feeds for the in-scope subway lines at a frequency sufficient to support reliable on-time/delay analysis, via a triggered polling pattern rather than a persistent continuous process. This is a deliberate architectural trade-off, not an unexamined limitation — see ADR-001 for the full options comparison and rationale. | Must |
| FR-2 | The system shall persist ingested real-time data durably, such that historical data is retained beyond the life of any single process run. | Must |
| FR-3 | The system shall load and retain the static GTFS reference data (routes, stops, trips, calendar) required to interpret real-time feed identifiers. | Must |
| FR-4 | The system shall compute, for each observed trip, whether it was on-time, delayed, or unable to be determined, based on comparison between scheduled and observed times. | Must |
| FR-5 | The system shall aggregate on-time performance by line, by station, and by time-of-day window. | Must |
| FR-6 | The system shall present a dashboard view showing overall on-time performance across the in-scope lines for a selectable date range. | Must |
| FR-7 | The system shall present a dashboard view showing on-time performance broken down by line. | Must |
| FR-8 | The system shall present a dashboard view showing where (which stations) and when (which time windows) delays concentrate. | Must |
| FR-9 | The system shall present a dashboard view showing reliability trend over the observed collection period. | Must |
| FR-10 | The system shall log ingestion failures (e.g., feed unreachable, malformed data) in a way that is reviewable after the fact, rather than failing silently. | Must |
| FR-11 | The system shall document data provenance, including that historical data reflects only the period during which this system was actively collecting, not a full agency-provided history. | Must |
| FR-12 | The system shall detect and surface anomalous shifts in delay levels (e.g., a sustained spike relative to recent baseline) as a distinct dashboard signal. | Should |
| FR-13 | The system shall allow the in-scope line set to be expanded via configuration without requiring a schema redesign. | Should |

"Must" requirements define MVP completion. "Should" requirements are valuable but not blocking for MVP sign-off; see Section 11.

---

## 6. Non-Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-1 | *(Revised — see ADR-001 in Architecture Document)* **Reliability of ingestion:** the ingestion process should recover automatically from transient failures (e.g., a single failed poll or workflow run) without manual intervention, within the execution model of the chosen ingestion platform (GitHub Actions). This includes explicit mitigation for platform-specific risks such as scheduled-workflow auto-disablement after prolonged repository inactivity. | Must |
| NFR-2 | **Data integrity:** ingested records should be validated against expected structure before being persisted; malformed records should be rejected and logged, not silently stored. | Must |
| NFR-3 | **Cost:** the system must run entirely on free-tier or self-hosted infrastructure — no paid services required to operate or demonstrate the project. | Must |
| NFR-4 | **Reproducibility:** a new contributor should be able to set up the full system (database, ingestion job, dashboard) from the repository and documentation alone, without undocumented manual steps. | Must |
| NFR-5 | **Maintainability:** code and schema should be organized and documented such that someone other than the original author can understand and extend it (per the standard established for this project). | Must |
| NFR-6 | **Dashboard responsiveness:** dashboard queries should return within a few seconds for the in-scope data volume, without requiring the user to understand the underlying schema. | Should |
| NFR-7 | **Compliance:** data collection and storage must operate within MTA's published usage terms (see Research Summary, prior phase). | Must |
| NFR-8 | **Observability:** the system should provide enough logging/metrics to answer "is the pipeline currently healthy?" without inspecting raw data manually. | Should |

---

## 7. Constraints

These are fixed conditions the project must operate within — not choices, but facts to design around.

| ID | Constraint | Source/rationale |
|---|---|---|
| C-1 | No budget for paid infrastructure or paid data access. | Portfolio project, self-funded |
| C-2 | MTA does not provide historical real-time data; only current/live feed state is available at any given request. | Confirmed in Research phase |
| C-3 | The NYCT GTFS-RT extension fields are not part of the core GTFS-RT spec and may be inconsistently populated. | Confirmed in Research phase |
| C-4 | Data collection and storage must comply with MTA's data usage terms (self-hosted storage required; no direct proxying of MTA's server; disclosure required if served data lags live MTA data by more than one minute). | Confirmed in Research phase |
| C-5 | Solo-developer project — no dedicated QA, design, or ops function; all roles performed by one person. | Project setup |
| C-6 | Timeline target is weeks, not months, for MVP completion, even though the broader portfolio effort may span longer. | Stated goal: maintain delivery momentum |

---

## 8. Assumptions

Assumptions are statements believed true at the time of writing that the project depends on, but which have not been independently verified end-to-end. Each is flagged so it can be revisited if proven false.

| ID | Assumption | Risk if false |
|---|---|---|
| A-1 | The MTA GTFS-Realtime subway feeds will remain accessible without an API key for the duration of the project. | Would require registering for a key and adjusting ingestion auth — low effort, but currently unverified for the full project duration |
| A-2 | Polling every ~30 seconds for the in-scope line subset will not trigger rate-limiting or access restrictions. | Would require backing off polling frequency, slightly reducing data granularity |
| A-3 | 4–6 weeks of continuously collected data will be sufficient to demonstrate meaningful trend analysis (FR-9). | If insufficient, trend claims in the dashboard would need to be scoped down or caveated |
| A-4 | The chosen in-scope line subset (to be finalized in Section 11) is representative enough to produce a credible reliability narrative, not a statistical edge case. | Would require expanding scope earlier than planned |
| A-5 | A single local (or free-tier hosted) PostgreSQL instance has sufficient capacity for several weeks of high-frequency positional data at the chosen scope. | Would require schema/retention adjustments; to be sized precisely in the Architecture Document |

---

## 9. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | MTA changes or deprecates the feed format or access policy mid-project (as has happened to other agencies, e.g., Metra in late 2025). | Low | High | Monitor MTA developer announcements; keep ingestion logic isolated so a feed-format change is a contained fix, not a rebuild |
| R-2 | Continuous ingestion job fails silently for an extended period (e.g., laptop sleeps, process crashes), creating a data gap. | Medium | Medium | FR-10 (failure logging) plus a simple health-check step run periodically during the collection window |
| R-3 | NYCT-specific protobuf extension fields are inconsistently documented, slowing implementation. | Medium | Medium | Budget explicit research/spike time for this in the Architecture phase rather than discovering it mid-build |
| R-4 | Scope creep — the temptation to add lines, modes, or ML forecasting before MVP is complete. | Medium | Medium | Section 11 (Out of Scope) is treated as binding for v1; new ideas go into Section 12 (Roadmap), not into active scope |
| R-5 | Collected historical window (4–6 weeks) is too short to show a compelling trend if reliability happens to be flat/stable during that period. | Medium | Low-Medium | Dashboard framing (FR-9) should present trend data honestly regardless of outcome — a stable trend is still a valid, correctly-measured finding, not a project failure |
| R-6 | Data storage volume grows faster than anticipated, given high-frequency polling across even a subset of lines. | Low-Medium | Medium | Address explicitly in Architecture Document via retention/aggregation strategy, informed by early volume observation during week 1 |

---

## 10. Success Metrics

**Product-level success metrics** (does the system do what it's supposed to do):

| Metric | Target |
|---|---|
| Ingestion uptime during the collection window | No unexplained gaps longer than a few missed polling cycles without a logged cause |
| Metric correctness | On-time/delay calculation verified accurate against a manually spot-checked sample of trips |
| Dashboard completeness | All "Must" functional requirements (Section 5) implemented and demonstrable |
| Historical data depth at project completion | At minimum, the full planned collection window (see Section 11) with no unexplained data holes |

**Portfolio-level success metrics** (does the project achieve its purpose as a career asset):

| Metric | Target |
|---|---|
| Comprehension speed | A reader unfamiliar with the project can state the business problem and what the dashboard shows within a short skim of the README |
| Cross-role legibility | The framing is understandable to Data Analyst, Business Analyst, Analytics Engineer, and Data Engineer reviewers without requiring transit-domain knowledge |
| Documentation completeness | PRD, Architecture Document, and README are internally consistent and each stands on its own |
| Process demonstration | The GitHub history and release notes reflect the staged process (Research → PRD → Architecture → UX → Implementation → Testing → Docs → Release), not a single dump commit |

---

## 11. MVP Scope

**In scope for v1:**
- **Line subset:** the numbered lines (1/2/3/4/5/6/7) — chosen because they form a coherent, well-known subset (the IRT division) rather than an arbitrary sample, keeping the reliability narrative easy to explain and the data volume manageable for a solo-developer, free-tier setup. *(This is a decision, not a placeholder — it can be revisited in Section 12 if early data volume suggests otherwise.)*
- GTFS-RT Trip Updates and Vehicle Positions feeds for that line subset
- Static GTFS reference data for schedule/dimension context
- Continuous ingestion for a defined collection window (target: 4–6 weeks, per the archiving decision made in Research phase)
- PostgreSQL storage with a normalized schema (design deferred to Architecture Document)
- SQL-based computation of on-time performance and delay metrics
- Streamlit dashboard covering FR-6 through FR-9 (and FR-12 if time allows, as a "Should")
- Automated tests covering the metric-computation logic
- README, this PRD, and an Architecture Document, all committed to the repository
- A tagged GitHub release marking MVP completion

**Definition of "collection window":** the 4–6 week continuous ingestion period begins as soon as the ingestion job is functional (targeted for early in the build, per the Research-phase decision to start archiving immediately) and runs in parallel with the rest of development — it is not a separate phase that blocks other work.

---

## 12. Out of Scope (v1) and Future Roadmap

Explicitly deferred, so that "should we add this" has a documented answer instead of being re-litigated mid-build.

| Item | Why deferred | Target for reconsideration |
|---|---|---|
| Full subway system (all lines) | Keeps v1 scope achievable solo, in weeks not months | v1.1 — natural, low-risk expansion once the pattern is proven |
| Bus, LIRR, Metro-North data | Different feed formats/characteristics; would dilute focus | v2 candidate, not committed |
| Weather or external data correlation | Adds API integration depth but is a distinct analytical question from reliability measurement | v1.1 stretch goal, previously discussed in Research |
| Predictive/ML delay forecasting | Requires a solid historical base (this project) as a prerequisite; is a strong *next portfolio project* on its own | Future, separate project |
| End-user alerting/notifications | Out of scope for an analytics tool aimed at operational insight, not consumer notification | Not currently planned |
| Multi-user auth/access control | This is a single-operator analytics tool, not a multi-tenant SaaS product | Not currently planned |
| Anomaly detection (FR-12) | Included as "Should," may slip to v1.1 if time-constrained | v1 stretch / v1.1 |

---

## 13. Acceptance Criteria

Each acceptance criterion maps directly to a functional requirement ID from Section 5, so completion is verifiable rather than subjective.

| AC ID | Maps to | Acceptance condition |
|---|---|---|
| AC-1 | FR-1 | Ingestion job runs unattended for the full collection window with logged evidence of successful polls at the expected cadence |
| AC-2 | FR-2 | Querying the database after a process restart returns previously ingested historical data intact |
| AC-3 | FR-3 | Real-time feed identifiers (route IDs, stop IDs, trip IDs) resolve correctly against static GTFS reference data in stored records |
| AC-4 | FR-4 | For a manually selected sample of trips, the system's on-time/delayed classification matches manual verification against the schedule |
| AC-5 | FR-5 | Aggregate queries return on-time performance broken down by line, station, and time-of-day window without manual post-processing |
| AC-6 | FR-6–FR-9 | Each specified dashboard view is present, populated with real collected data (not placeholder/sample data), and navigable without documentation |
| AC-7 | FR-10 | A deliberately induced ingestion failure (e.g., simulated network error) produces a reviewable log entry rather than a silent gap |
| AC-8 | FR-11 | README and dashboard both state the data collection start date and clarify that history reflects only the collection window |
| AC-9 | FR-12 (Should) | If implemented: a manually introduced or naturally occurring delay spike is visibly flagged on the dashboard |
| AC-10 | FR-13 (Should) | If implemented: adding a new line to configuration does not require modifying the database schema |
| AC-11 | NFR-4 | A clean environment, following only the README setup steps, results in a working system without undocumented manual fixes |
| AC-12 | NFR-7 | Data handling practices documented in the README are consistent with MTA's published usage terms as confirmed in Research |

**MVP is considered complete when all AC items mapped to "Must" requirements (Section 5) pass.** "Should"-mapped AC items (AC-9, AC-10) are desirable but non-blocking.

---

## 14. Open Questions

Documented rather than silently resolved, so the reasoning trail is visible to a future reader.

| Question | Status |
|---|---|
| Should the anomaly-detection feature (FR-12) use a simple statistical threshold or something more sophisticated? | Deferred to Architecture Document — this PRD only establishes that the *capability* is desired at "Should" priority, not the method |
| What retention/aggregation strategy prevents unbounded database growth over the collection window? | Deferred to Architecture Document (flagged in Risk R-6) |
| Exact dashboard layout and navigation flow | Deferred to UX Plan (next phase after this PRD) |

---

## 15. Explicit Non-Coverage Statement

Per the working agreement for this project: this document does not address database schema design, technology-specific implementation choices beyond what's already fixed by prior agreement (PostgreSQL, Python, Streamlit), infrastructure/hosting specifics, or UI layout. Those belong to the Architecture Document and UX Plan, respectively, which will reference the requirement IDs defined here.
