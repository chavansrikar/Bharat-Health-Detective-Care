---
title: Bharat Health Detective Care
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
python_version: "3.10"
license: mit
---

# Bharat Health Detective Care

**Healthcare operations and public-health intelligence — simulated demonstration platform.**

Bharat Health Detective Care is a working prototype of an integrated district health operations workspace and a
separate public-facing citizen portal. It demonstrates how facility infrastructure, workforce, preventive
programmes, screening, diagnostics, referrals, communications and employment data can be coordinated through one
governed operating picture.

The default experience is the administrative **Healthcare Overview**, not a patient home screen. The Citizen Portal
is a secondary, consent-led experience.

> **Simulated data — not for clinical use.** Every facility, person and activity record is fictional. This
> application is not a medical device, clinical decision system, government service or production patient-record
> platform. Do not enter real patient information.

---

## 1. What the platform demonstrates

| Domain | Implemented capability |
|---|---|
| Operations overview | Scoped KPIs, operational alerts, access-gap view, four live Plotly charts |
| Infrastructure | Facility search and filters, detail panel, creation, status updates, service catalogue |
| Locator and mapping | Schematic facility map with district, service and locality filters |
| Utilisation analytics | Documented attendance/capacity formula with contextual indicators |
| Workforce | Staff roster, availability, skills, unfilled posts, vacancy and application control |
| Preventive programmes | Programme metadata, screening event planning and completion tracking |
| Screening operations | Synthetic participant registration, observation capture, clinician review queue |
| Diagnostics | Diagnostic order list and report-status workflow with no fabricated clinical values |
| Citizen registry | Synthetic participant profiles, consent state and limited operational history |
| Referral coordination | Enforced state machine, priority handling, urgent-destination safety rule, overdue detection |
| Awareness campaigns | Draft campaign creation with explicitly simulated delivery |
| Notifications | Internal notification drafts and simulated delivery status |
| Substance-use prevention | Voluntary, confidential, consent-gated counselling support cases |
| Healthcare employment | Vacancy management and application pipeline |
| Reports and analytics | Scoped summary rates, 12 CSV datasets, combined ZIP export |
| Administration | Dataset counts, role matrix, recent activity log, deterministic demo reset |
| Citizen portal | Profile, reminders, service finder, appointment requests, records and awareness feed |

Every metric and table is computed from the local SQLite database. No KPI is hard-coded in the interface.

---

## 2. Roles and navigation

Role switching is a **demonstration control, not authentication**. It changes navigation and the visible workspace.
It does not enforce permissions, protect data or represent a production access-control model.

| Role | Primary focus |
|---|---|
| District Administrator (default) | Full district operations, reports and administration |
| State Health Administrator | State-wide operations, reports and administration |
| District Medical Officer | Clinical review, referrals, programmes, diagnostics and reports |
| Facility Administrator | Infrastructure, workforce, diagnostics and local reporting |
| Medical Officer | Screening review, referrals, diagnostics and citizen records |
| Laboratory Administrator | Diagnostic laboratory workflow and reports |
| Community Health Worker | Registry, screening, referrals, campaigns and citizen support |
| Citizen | Citizen Portal and facility locator only |

The interface keeps simulated-data, demo-role and safety notices visible throughout the session. See
`src/config.py` for the role list and `app.py` for the navigation mapping.

---

## 3. Screens

1. **Healthcare Overview** — scoped KPIs, alerts, facility mix, referral status, screening trend, utilisation and
   mandal access gaps.
2. **Infrastructure Management** — searchable facility directory, detail view, facility creation, status updates
   and service additions.
3. **Facility Locator and Mapping** — service and locality search with a schematic coordinate map.
4. **Facility Utilization Analytics** — configured capacity vs completed screening attendance, indicators and
   planning gaps.
5. **Medical Workforce Management** — staff roster, availability filters, staffing gaps, vacancies and vacancy
   updates.
6. **Preventive Health Programmes** — programme catalogue, programme creation, event planning and attendance.
7. **Screening Operations** — participant registration, observation recording and clinician review queue.
8. **Diagnostic Laboratory Management** — order filters, report entry, verification, delivery and review counts.
9. **Patient and Citizen Registry** — synthetic participant lookup with operational history and referral context.
10. **Referral Coordination** — queue filters, creation, valid transitions, follow-up dates and overdue detection.
11. **Health Awareness Campaigns** — campaign drafts, approval state and simulated delivery.
12. **Notification Management** — internal notification drafts and simulated channel status.
13. **Substance-Use Prevention** — confidential support cases, consent capture, counselling status and aggregate
    demand view.
14. **Healthcare Employment** — vacancy list, vacancy creation and application pipeline.
15. **Reports and Analytics** — scoped reporting, service utilisation, staffing gaps and exports.
16. **Administration and Settings** — environment statement, dataset counts, role intent, audit events and reset.
17. **Citizen Portal** — citizen profile, reminders, facility finder, appointment requests, records and awareness
    content.

---

## 4. Architecture

```
Gradio Blocks UI (src/ui)
        |
        v
Service layer (src/services)
  facility · screening · referral · laboratory · reporting
  workforce · notification · substance · citizen · optional AI
        |
        v
SQLAlchemy ORM models (src/models)  -->  SQLite demo database (data/)
```

- UI callbacks contain no SQL. They call service functions inside a transactional session scope.
- The service layer owns validation, workflow rules, scoping and derived metrics.
- The optional AI adapter is disabled by default and returns deterministic, grounded fallbacks when unconfigured.
- Configuration is environment-driven; no secrets belong in source.
- The database is created and seeded deterministically on startup if empty.

### Technology stack

| Layer | Choice |
|---|---|
| UI | Gradio 5 Blocks |
| Language | Python 3.10+ |
| Database | SQLite |
| ORM | SQLAlchemy 2 |
| Validation | Pydantic (installed for schema extension) |
| Analysis | Pandas |
| Charts | Plotly |
| Tests | pytest |
| Hosting | Hugging Face Spaces (Gradio SDK) |

---

## 5. Demo dataset and metric definitions

The deterministic seed contains:

| Entity | Count |
|---|---|
| Facilities | 30 |
| Services | 95 |
| Synthetic participants | 40 |
| Programmes | 4 |
| Screening events | 7 |
| Screening observations | 30 |
| Referrals | 16 |
| Laboratory orders | 12 |
| Staff | 22 |
| Vacancies | 18 |
| Employment applications | 10 |
| Campaigns | 6 |
| Notifications | 6 |
| Substance-use support cases | 8 |
| Appointment requests | 8 |

All records are fictional. Participant identifiers are synthetic codes and aliases; no Aadhaar, ABHA, phone number
or real clinical record is stored.

### Core formulas

| Metric | Definition |
|---|---|
| Screening utilisation | Attendance recorded at completed screening events divided by summed active preventive/screening service capacity, averaged over facilities with both values. A planning indicator, not a quality score. |
| Catchment coverage | Catchment population of active facilities divided by total catchment population in scope. |
| Referral completion | Completed referrals divided by referrals sent (excluding draft and cancelled). |
| Follow-up completion | Completed referrals with a follow-up date divided by referrals with a follow-up date that were not draft or cancelled. |
| Screening review rate | Reviewed screening observations divided by all screening observations in scope. |
| Staffing gap | Sum of `max(required_count - filled_count, 0)` across vacancies in scope. |
| Access gap | A mandal with no active facility, or no active primary-care-or-higher facility. |
| Operational alerts | Derived from inactive facilities, overdue follow-ups, staffing gaps, pending reports, pending reviews, pending verification and access gaps. |

Utilisation labels are contextual: `No screening activity recorded`, `No configured capacity`, `Spare capacity`,
`Balanced`, `Near capacity`. None of these labels implies clinical quality or patient outcomes.

---

## 6. Safety, privacy and governance rules

1. **Screening is not diagnosis.** Observations are labelled as screening findings and require clinician review.
2. **Emergency escalation is never delayed.** Urgent referrals are rejected unless the destination is an
   emergency-capable facility type or has active emergency care.
3. **No fabricated clinical results.** Laboratory screens show workflow status only; no invented values.
4. **Synthetic data only.** No real identifiers, contact details or clinical records.
5. **Minimum necessary data.** The registry and citizen portal show limited operational information only.
6. **Consent is explicit.** Citizen profiles and substance-use support cases require recorded consent.
7. **Substance-use support is voluntary and non-punitive.** The module must not be used for enforcement,
   employment or disciplinary decisions.
8. **No real messaging.** Campaigns and notifications are drafts or simulated; nothing is sent.
9. **Appointments are requests.** The portal records a requested slot and instructs the citizen to confirm with the
   facility; it does not confirm availability or book clinical appointments.
10. **No AI diagnosis or prescribing.** The optional assistant is limited to administrative summaries, navigation
    explanations and campaign drafts, with human review.
11. **Role switching is not authentication.** Production deployment requires an identity provider, MFA and scoped
    authorization.
12. **Core workflows work without an LLM.** Deterministic paths are the default.

---

## 7. Local setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:7860>. The database is created and seeded on first start. Use
**Administration and Settings → Restore deterministic demo dataset** to reset the demo.

### Running tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The suite uses an isolated temporary SQLite database and covers:

- deterministic seed counts and idempotent seeding;
- facility search, filtering, creation and utilisation fields;
- screening recording, review and double-review rejection;
- referral lifecycle, invalid transitions, urgent-destination safety and overdue detection;
- laboratory review and report delivery rules;
- workforce summaries, vacancies and application workflow;
- citizen consent, appointment lifecycle and invalid booking rejection;
- campaigns, notifications and substance-use confidentiality/validation;
- scoped KPIs, CSV exports and deterministic reset.

---

## 8. Deploying to Hugging Face Spaces

The repository is configured for the **Gradio SDK**:

- `app.py` is the root entry point.
- `requirements.txt` pins runtime dependencies.
- README frontmatter declares `sdk: gradio`, `sdk_version: 5.50.0`, `app_file: app.py`, `python_version: 3.10`.
- The app binds to `0.0.0.0` and reads the platform `PORT` (default `7860`).
- SQLite is created at startup; if the repository directory is read-only, the app falls back to a writable temp
  path.
- Demo data is re-seeded automatically when the database is empty.

### Steps

1. Create a new Space with **SDK: Gradio**.
2. Push this repository's contents to the Space.
3. Wait for the build; the Space runs `python app.py`.
4. Open the Space URL. No secrets are required for core workflows.

### Deployment notes

- Spaces storage is ephemeral unless a persistent volume is attached. Demo edits may be lost on restart; the seed
  restores a clean baseline.
- Do not upload real health data, real identifiers or secrets to a public Space.
- Keep `BHDC_AI_ENABLED=0` unless an approved provider adapter and governance process exist.
- Re-run the test suite after dependency upgrades.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `BHDC_DB_PATH` | `data/bharat_health.db` | SQLite database path |
| `BHDC_SERVER_NAME` | `0.0.0.0` | Bind address |
| `BHDC_SERVER_PORT` / `PORT` | `7860` | Bind port |
| `BHDC_AI_ENABLED` | `0` | Enables optional AI adapter |
| `BHDC_AI_API_KEY` | empty | Provider key (never commit) |
| `BHDC_AI_MODEL` | `opencode/big-pickle` | Optional model label |

---

## 9. Repository layout

```
bharat-health-detective-care/
├── app.py                     # Gradio entry point, navigation, role mapping, startup seed
├── requirements.txt           # Runtime dependencies (pinned)
├── requirements-dev.txt       # Test dependencies
├── conftest.py                # Isolated test database bootstrap
├── opencode.json              # Optional coding-model selection
├── .env.example               # Environment variable template
├── data/                      # SQLite database created at runtime
├── docs/
│   └── PROJECT_DOCUMENTATION.md
├── src/
│   ├── config.py              # Settings, roles, geography, taxonomies, statuses
│   ├── database.py            # Engine, session scope, schema init
│   ├── seed.py                # Deterministic synthetic dataset and reset
│   ├── models/                # SQLAlchemy models by domain
│   ├── services/              # Business logic, workflows and reporting
│   └── ui/                    # 17 Gradio screens, theme and shared components
└── tests/                     # Workflow, safety and reporting tests
```

---

## 10. Demo walkthrough

1. Open **Healthcare Overview** and review KPIs, alerts, charts and mandal access gaps.
2. Filter **Infrastructure Management** by state, district, category and service; open a facility detail.
3. Review **Facility Utilization Analytics** for spare capacity and facilities with no screening activity.
4. In **Medical Workforce Management**, inspect unfilled posts and open vacancies.
5. In **Preventive Health Programmes**, create a programme and a screening event.
6. In **Screening Operations**, register a synthetic participant and record an observation for clinician review.
7. In **Diagnostic Laboratory Management**, move an order through report entry, verification and delivery.
8. In **Referral Coordination**, create a referral and advance it through the permitted state sequence.
9. In **Health Awareness Campaigns** and **Notification Management**, draft simulated communications.
10. In **Substance-Use Prevention**, optionally create a consented, confidential support case.
11. In **Healthcare Employment**, create a vacancy and progress an application.
12. In **Reports and Analytics**, generate a scoped CSV or the combined ZIP archive.
13. Switch to **Citizen** and use the **Citizen Portal** for reminders, facility search and an appointment request.
14. Use **Administration and Settings** to inspect counts and restore the deterministic dataset.

---

## 11. Known limitations

- Role switching is not authentication and provides no real access control.
- All data is fictional and local; there is no multi-tenancy, encryption-at-rest or retention policy.
- Facility availability is not live and must be confirmed directly.
- Notifications and campaigns are simulated; nothing is sent.
- Appointment requests are not confirmed bookings.
- No ABDM/ABHA, HMIS, eSanjeevani, laboratory, pharmacy, payment or entitlement integration.
- No clinical decision support, diagnosis, prescribing or treatment planning.
- Utilisation, coverage and gap metrics are illustrative planning indicators, not measured impact.
- SQLite is not suitable for concurrent production use.
- The optional AI adapter is off by default and unsuited to clinical use.

---

## 12. License

Released under the MIT License. See `LICENSE` for details.
# Bharat-Health-Detective-Care
