# Bharat Health Detective Care — Project Documentation

**Version:** 2.0 (enterprise operations baseline)
**Status:** Working simulated-data prototype
**Primary demo geography:** Telangana (illustrative), including Yadadri Bhuvanagiri, Nalgonda and Medchal-Malkajgiri
**Document purpose:** Functional reference, architecture record, data and metric definitions, safety specification,
deployment guide and scalability plan for contributors and reviewers.

> **Simulated data — not for clinical use.** All facilities, people, services and activity records are fictional.
> This application is not a medical device, clinical decision system, government service or production
> patient-record platform.

---

## Table of contents

1. [Product summary](#1-product-summary)
2. [Scope and non-goals](#2-scope-and-non-goals)
3. [Roles and navigation](#3-roles-and-navigation)
4. [Module specification](#4-module-specification)
5. [Workflows and state machines](#5-workflows-and-state-machines)
6. [Data model](#6-data-model)
7. [Metrics and reporting](#7-metrics-and-reporting)
8. [Service layer contracts](#8-service-layer-contracts)
9. [Safety, privacy and governance](#9-safety-privacy-and-governance)
10. [Architecture, configuration and deployment](#10-architecture-configuration-and-deployment)
11. [Testing and quality](#11-testing-and-quality)
12. [Operations and demo reset](#12-operations-and-demo-reset)
13. [Scalability roadmap](#13-scalability-roadmap)
14. [Known limitations](#14-known-limitations)
15. [Glossary](#15-glossary)

---

## 1. Product summary

Bharat Health Detective Care is a simulated healthcare-operations and public-health intelligence platform. It
brings facility infrastructure, workforce, preventive programmes, screening activity, diagnostic workflow, referral
coordination, communications, employment and citizen-facing navigation into one coherent operating picture.

The design premise is to make **existing** capacity discoverable and better coordinated rather than to create
another isolated patient application. The default landing experience is the administrative **Healthcare Overview**
for the District Administrator. The **Citizen Portal** is a separate, secondary experience.

### Core operating loop

> **Inspect the network → identify a gap → plan a preventive activity → record a screening observation →
> review it clinically → refer when appropriate → track diagnostic and referral follow-up → report the outcome.**

### Primary value

- Make facilities, services, workforce and preventive programmes discoverable in one workspace.
- Support appropriate use of configured service capacity.
- Coordinate preventive screening with explicit clinician review.
- Track referral, laboratory and follow-up status to completion.
- Give administrators a scoped operational picture with documented metric definitions.
- Provide citizens with a consent-led route to find listed services and request appointments.

### What it is not

- Not a medical device or clinical decision system.
- Not a government service or official district system.
- Not a production patient-record platform.
- Not a diagnostic, prescribing or treatment tool.
- Not connected to ABDM, ABHA, HMIS, eSanjeevani, laboratory or pharmacy systems.
- Not an authentication or authorization system; the role switcher is a demonstration control.
- Not evidence of measured health impact, cost savings or improved outcomes.

---

## 2. Scope and non-goals

### In scope

- Scoped operational KPIs, alerts and access-gap analysis.
- Facility directory with search, filters, detail, creation, status updates and service cataloguing.
- Facility locator with schematic mapping.
- Utilisation indicator based on a documented attendance/capacity formula.
- Workforce roster, availability, staffing gaps, vacancies and vacancy updates.
- Preventive programme and screening event planning.
- Screening participant registration, observation capture and clinician review queue.
- Diagnostic order and report-status workflow with no fabricated clinical values.
- Synthetic participant registry with operational context.
- Referral creation, enforced state transitions, follow-up dates and overdue detection.
- Campaign and notification drafting with simulated delivery only.
- Voluntary, confidential substance-use support cases with consent capture.
- Healthcare vacancy and employment application pipeline.
- Scoped reporting, CSV exports and a combined ZIP archive.
- Administration view with dataset counts, role intent, audit events and deterministic reset.
- Citizen portal with profile, reminders, service finder, appointment requests, records and awareness feed.
- Eight demo roles with role-specific navigation and persistent safety notices.

### Explicit non-goals

- No real patient identifiers, Aadhaar numbers, ABHA IDs, phone numbers or clinical records.
- No live integration with government, hospital, laboratory or pharmacy systems.
- No real SMS, WhatsApp, voice, payment or entitlement actions.
- No AI diagnosis, image interpretation, medicine recommendation or autonomous treatment planning.
- No production authentication, authorization, encryption-at-rest or retention policy.
- No claim of measured impact, compliance certification or production readiness.
- No use of substance-use data for enforcement, employment or disciplinary decisions.

---

## 3. Roles and navigation

The application exposes eight demo roles. Selecting a role changes the available navigation and the active screen,
and displays a persistent demo-role warning.

| Role | Primary focus | Navigation scope |
|---|---|---|
| District Administrator (default) | Full district operations | All 17 screens |
| State Health Administrator | State-wide operations | All 17 screens |
| District Medical Officer | Clinical and operational oversight | All screens except Administration and Settings |
| Facility Administrator | Local infrastructure and workforce | All screens except Administration and Settings |
| Medical Officer | Clinical review and follow-up | Overview, locator, prevention, screening, diagnostics, registry, referrals, substance-use, campaigns, reports, citizen portal |
| Laboratory Administrator | Diagnostic operations | Overview, diagnostics, registry, referrals, notifications, reports, citizen portal |
| Community Health Worker | Outreach and citizen support | Overview, locator, prevention, screening, registry, referrals, campaigns, substance-use, citizen portal |
| Citizen | Public experience | Citizen Portal and Facility Locator only |

### Role caveat

The role switcher is **not authentication**. It does not enforce permissions, restrict queries, protect records or
represent production access control. Every role can access the same underlying demo database through the available
service-layer screens. Production deployment requires an identity provider, multi-factor authentication, scoped
RBAC/ABAC and audited authorization decisions.

The default session opens as **District Administrator** on **Healthcare Overview**.

---

## 4. Module specification

### 4.1 Healthcare Overview

**Purpose:** Provide a scoped operational snapshot for administrators.

**Content and actions**

- Scope controls: state, district, mandal, facility category and active status.
- KPI cards: facilities in scope, active facilities, inactive records, average screening utilisation, listed
  services, available staff, unfilled posts, screening observations, pending reports, open referrals, follow-up
  completion and catchment coverage.
- Derived operational alerts by severity.
- Charts: facilities by type, referral status distribution, screening observations by month and screening
  utilisation by facility.
- Access-gap table by mandal.

**Notes:** Utilisation is a planning indicator, not a clinical quality score. Access gaps do not measure travel
time, population need or service quality.

### 4.2 Infrastructure Management

**Purpose:** Maintain the facility directory and service catalogue.

**Content and actions**

- Search by name, locality, type, district or address.
- Filters for facility type, mandal, service, verification status, operating status and active status.
- Facility detail panel.
- Create a facility with required name, type, mandal and locality.
- Update operating status, active flag, verification status, bed count, catchment population and capacity notes.
- Add a service with capacity and availability note.

**Safety:** New facilities default to pending verification. Creating a record does not establish that a facility or
service exists.

### 4.3 Facility Locator and Mapping

**Purpose:** Help administrators and citizens find facilities by service and locality.

**Content and actions**

- State, district, facility category, service and free-text filters.
- Results table and facility detail.
- Schematic coordinate map for matching active facilities.
- Emergency notice and confirm-before-travelling guidance.

**Notes:** The map is illustrative and not a routing or travel-time service.

### 4.4 Facility Utilization Analytics

**Purpose:** Compare completed screening attendance with configured preventive-service capacity.

**Content and actions**

- Facility-level capacity, completed attendance, utilisation percentage and indicator.
- Aggregate indicators and chart.
- Facilities with spare capacity, near-capacity operation or no recorded activity.

**Formula:** Attendance at completed screening events divided by summed active preventive/screening service
capacity for the same facility. See section 7. The indicator is not a measure of clinical quality, efficiency or
patient outcomes.

### 4.5 Medical Workforce Management

**Purpose:** Coordinate staff visibility, staffing gaps and vacancy control.

**Content and actions**

- Staff roster with role, qualification, facility, skills, availability, shift, employment type and verification.
- Filters by role, availability and free text.
- Staffing-gap table and chart derived from configured vacancies.
- Create a vacancy with required count and priority.
- Update filled count and vacancy status.

**Notes:** Availability reflects the demo roster, not live attendance. Unfilled posts require verification before
real deployment decisions.

### 4.6 Preventive Health Programmes

**Purpose:** Plan programmes and screening events.

**Content and actions**

- Programme catalogue with cohort, eligibility notes, guidance reference and date range.
- Create a programme.
- Create a screening event against a programme and facility, with date, name and planned status.
- Event list with attendance where completed.

**Safety:** Programme and event metadata support coordination only; they do not define clinical protocols.

### 4.7 Screening Operations

**Purpose:** Register synthetic participants, record screening observations and complete clinician review.

**Content and actions**

- Register a participant with synthetic alias, age band, gender, locality and consent status.
- Record a screening observation with screening type, free-text observation, result category and review status.
- Priority-ordered review queue.
- Record reviewer identity and review outcome.

**Safety:** A screening observation is not a diagnosis. Result categories require clinician review and confirmation.
No images, investigations or prescriptions are generated.

### 4.8 Diagnostic Laboratory Management

**Purpose:** Track diagnostic orders and report workflow without displaying clinical values.

**Content and actions**

- Order list with facility and status filters.
- Workflow actions to enter a result, verify a report, mark clinician review and deliver a report.
- Pending report, awaiting-review and report-status distribution views.

**Safety:** The module stores workflow metadata only. No invented laboratory values are generated or displayed.

### 4.9 Patient and Citizen Registry

**Purpose:** Provide a limited operational registry for synthetic participants.

**Content and actions**

- Participant search and selection.
- Profile detail with consent state and assigned worker.
- Related screening, referral, laboratory and appointment context.
- Operational timeline summary.

**Safety:** The registry contains synthetic codes and aliases only. It is not a clinical record and must not be
used for identity verification.

### 4.10 Referral Coordination

**Purpose:** Coordinate referral status and follow-up.

**Content and actions**

- Queue filters for status, priority and overdue referrals.
- Create a referral with source, destination, reason, priority, referring doctor and follow-up date.
- Advance referrals through permitted transitions.
- Record closure note on completion.
- Overdue detection for follow-ups past the due date.

**Safety:** Urgent referrals are rejected unless the destination is an emergency-capable facility type or has
active emergency care.

### 4.11 Health Awareness Campaigns

**Purpose:** Draft and track simulated public-health communications.

**Content and actions**

- Campaign list filtered by status and channel.
- Create a campaign with title, message, language, audience, target area, channel, schedule and responsible
  facility.
- Update campaign status through draft and approval states.

**Safety:** No message is sent. Campaign delivery is explicitly simulated, and content requires human review.

### 4.12 Notification Management

**Purpose:** Draft internal notification records and track simulated delivery.

**Content and actions**

- Notification list filtered by status and channel.
- Create a notification with title, message, audience, channel, related entity and schedule.
- Update status through draft, approval and simulated-sent states.

**Safety:** No real SMS, voice, WhatsApp or notice-board delivery occurs.

### 4.13 Substance-Use Prevention

**Purpose:** Support voluntary, confidential, non-punitive counselling coordination.

**Content and actions**

- Confidential support case list with aggregate demand chart.
- Create a case only with recorded consent.
- Track counselling status, assigned counsellor and follow-up date.
- Update status and notes.

**Safety:** The module must not be used for enforcement, criminal, employment or disciplinary decisions. It never
labels a person, and clinical decisions remain with qualified clinicians.

### 4.14 Healthcare Employment

**Purpose:** Coordinate healthcare vacancy and application pipelines.

**Content and actions**

- Vacancy list with required/filled counts, gap, status and priority.
- Create vacancies against facilities.
- Application list with role, qualification, experience and status.
- Create applications and advance them through the pipeline.

**Notes:** Applicant records use aliases only and are not a recruitment system of record.

### 4.15 Reports and Analytics

**Purpose:** Produce scoped operational summaries and data extracts.

**Content and actions**

- Scope controls and summary KPI cards.
- Service utilisation table, facility-type table, referral-status table and staffing-gap table.
- Export one of 12 datasets as CSV.
- Export all available datasets as a ZIP archive.

**Safety:** Exports contain synthetic demo records only. Generated files are written to a temporary directory.

### 4.16 Administration and Settings

**Purpose:** Provide demo governance, configuration transparency and reset controls.

**Content and actions**

- Environment and safety statement.
- Dataset row counts for all 16 tables.
- Demo role access matrix.
- Recent audit events.
- Confirm-by-typing reset of the deterministic dataset.

**Safety:** The role matrix describes navigation intent, not enforced authorization.

### 4.17 Citizen Portal

**Purpose:** Provide a separate, consent-led public experience.

**Content and actions**

- Create or select a synthetic citizen profile with consent.
- View reminders, appointment requests and operational records.
- Search facilities by district and service.
- Request an appointment and cancel a request.
- Browse approved awareness campaigns and notifications.

**Safety:** Emergency symptoms require immediate emergency care. Appointment requests are not confirmed bookings.
The portal is not a medical service and does not verify identity.

---

## 5. Workflows and state machines

### 5.1 Facility lifecycle

1. A facility is created with pending verification and a default operating status.
2. An administrator updates operating status, active flag, verification status, beds, catchment or capacity notes.
3. Services are added with capacity and availability notes.
4. Inactive facilities are excluded from active-scope metrics and citizen search.

No hard delete is exposed in the UI.

### 5.2 Programme and screening event lifecycle

- Programmes are created with a name, cohort, eligibility notes, guidance reference and date range.
- Screening events are created against a programme and facility with a planned date.
- Completed events carry an attendance count used by the utilisation indicator.
- Screening observations are recorded against an event and participant.

### 5.3 Screening review

Result categories: `Normal`, `Needs clinician review`, `Urgent review`.

Review statuses:

| Status | Meaning |
|---|---|
| Pending clinician review | Awaiting qualified review |
| Reviewed | Reviewed and recorded |
| Returned for clarification | Review requires clarification |

A screening already reviewed cannot be reviewed again by the current service rule.

### 5.4 Referral state machine

| Current status | Permitted next statuses |
|---|---|
| Draft | Sent, Cancelled |
| Sent | Accepted, Returned for clarification, Cancelled |
| Accepted | Scheduled, Cancelled |
| Scheduled | Attended, Cancelled, Returned for clarification |
| Attended | Completed |
| Completed | None |
| Returned for clarification | Sent, Cancelled |
| Cancelled | None |

**Urgent safety rule:** when priority is `Urgent`, the destination must be a CHC, District Hospital, Medical College
Hospital or participating private hospital, or have an active `Emergency care` service. Otherwise creation is
rejected.

**Overdue:** a referral with a follow-up date before today and a status in Sent, Accepted, Scheduled or Returned for
clarification is treated as overdue.

### 5.5 Laboratory workflow

Sample/order statuses:

`Ordered → Sample collected → Received by lab → Processing → Result available → Clinician reviewed`

Report statuses:

| Status | Meaning |
|---|---|
| Pending result entry | No result metadata entered |
| Result entered | Result metadata recorded; awaiting verification |
| Verified | Report verified; awaiting clinician review/delivery |
| Delivered | Report workflow complete |

Reviewer status defaults to `Awaiting clinician review` and becomes reviewed after the review step. Laboratory
records contain status metadata only.

### 5.6 Workforce and employment

Vacancy statuses: `Open`, `Partially filled`, `Filled`, `On hold`.
Vacancy priorities: `High`, `Routine`.
Application statuses: `Received`, `Shortlisted`, `Interview scheduled`, `Offer`, `Rejected`, `Withdrawn`.

The staffing gap is calculated as `max(required_count - filled_count, 0)` per vacancy.

### 5.7 Campaigns and notifications

Campaign statuses: `Draft`, `Needs review`, `Approved draft`, `Scheduled (simulated)`.
Notification statuses: `Draft`, `Approved`, `Simulated — sent`, `Cancelled`.

Delivery status is always simulated. No external provider is called.

### 5.8 Substance-use support

Statuses: `Screening recorded`, `Counselling scheduled`, `Counselling completed`, `Referred`, `Closed`.

Creation requires consent. Records carry a restricted confidentiality level and are presented as voluntary,
non-punitive support.

### 5.9 Citizen appointments

Statuses: `Requested`, `Confirmed`, `Attended`, `Cancelled`, `Missed`.

The portal creates `Requested` records only and never confirms availability. A requested appointment can be
cancelled in the demo. Past dates and inactive facilities are rejected.

---

## 6. Data model

The local SQLite database contains 16 tables. All records are synthetic.

| Table | Purpose | Key relationships |
|---|---|---|
| `facilities` | Facility registry and operational status | Services, staff, events, referrals, lab orders, vacancies, appointments |
| `services` | Service catalogue and configured capacity | Belongs to facility |
| `participants` | Synthetic citizen/participant profiles | Screenings, referrals, substance cases, appointments |
| `staff` | Workforce roster | Optional facility assignment |
| `programmes` | Preventive programme metadata | Screening events |
| `screening_events` | Planned/completed screening activities | Programme and facility; screenings |
| `screenings` | Screening observations and review state | Participant and event; optional referral link |
| `referrals` | Referral coordination records | Source/destination facilities, participant, screening, lab orders |
| `lab_orders` | Diagnostic workflow metadata | Referral and laboratory facility |
| `campaigns` | Awareness campaign drafts | Optional responsible facility |
| `notifications` | Internal notification drafts | Related entity text |
| `audit_events` | Lightweight in-app activity log | Free-form entity reference |
| `substance_use_cases` | Confidential support cases | Participant |
| `staff_vacancies` | Configured staffing gaps | Facility |
| `employment_applications` | Application pipeline | Optional facility |
| `appointments` | Citizen appointment requests | Participant and facility |

### Important field notes

- `Facility.code` is unique. Facility type maps to a planning category through `FACILITY_CATEGORY_MAP`.
- `Facility.verification_status` and `operating_status` are operational metadata, not authoritative facts.
- `ScreeningEvent.attendance_count` drives the utilisation indicator.
- `Screening.observation_text` is free text and must be treated as a screening note, not a diagnosis.
- `Referral.referring_doctor` records the demo clinician associated with the referral.
- `LabOrder.demo_result_note` explicitly states that no clinical value is stored.
- `SubstanceUseCase.consent_status` and `confidentiality_level` are mandatory safety context.
- `Appointment.contact_preference` is a demo preference; no contact is made.

### Seed counts

| Entity | Count |
|---|---|
| Facilities | 30 |
| Services | 95 |
| Participants | 40 |
| Programmes | 4 |
| Screening events | 7 |
| Screenings | 30 |
| Referrals | 16 |
| Laboratory orders | 12 |
| Staff | 22 |
| Vacancies | 18 |
| Applications | 10 |
| Campaigns | 6 |
| Notifications | 6 |
| Substance-use cases | 8 |
| Appointments | 8 |

Seeding is idempotent: if data already exists, `seed_database` does not duplicate it. `reset_database` removes
existing rows and recreates the deterministic dataset.

---

## 7. Metrics and reporting

All metrics are computed from the local database for the selected scope. Scope filters are state, district,
mandal, facility category and active status. Dependent records are scoped through their facility.

| Metric | Definition |
|---|---|
| Facilities in scope | Count of facility records matching scope filters |
| Active facilities | Count where `is_active` is true |
| Inactive records | Count where `is_active` is false |
| Services listed | Count of active service records for facilities in scope |
| Staff in scope | Count of staff assigned to facilities in scope |
| Staff available | Staff with availability `Available` or `On duty` |
| Staffing gaps | Sum of unfilled posts across vacancies in scope |
| Screening events | Count of events for facilities in scope |
| Screening observations | Count of screenings linked to events in scope |
| Pending screening reviews | Screenings with status `Pending clinician review` |
| Screening review rate | Reviewed observations divided by all observations in scope |
| Referrals total | Referrals with a source facility in scope |
| Open referrals | Referrals in Draft, Sent, Accepted, Scheduled or Returned for clarification |
| Referral completion | Completed referrals divided by referrals not Draft or Cancelled |
| Follow-up completion | Completed referrals with a follow-up date divided by referrals with a follow-up date not Draft or Cancelled |
| Follow-ups overdue | Follow-up date before today with an active referral status |
| Pending reports | Laboratory orders not yet Delivered |
| Laboratory awaiting review | Orders with reviewer status `Awaiting clinician review` |
| Catchment coverage | Catchment population of active facilities divided by total catchment population in scope |
| Pending verification | Facilities whose verification status is not Verified |

### Screening utilisation

**Formula:** for each facility, sum of attendance recorded at completed screening events divided by the sum of
active preventive/screening service capacity. The dashboard reports the average across facilities with both a
positive configured capacity and completed activity.

Capacity is selected from active services whose names match preventive/screening keywords:
`screening`, `maternal`, `child`, `counselling`, `wellness`, `nutrition`.

**Indicators**

| Condition | Indicator |
|---|---|
| No completed attendance | No screening activity recorded |
| Positive attendance but zero configured capacity | No configured capacity |
| Utilisation ≥ 90% | Near capacity |
| Utilisation ≥ 40% | Balanced |
| Utilisation < 40% | Spare capacity |

This is an operational planning indicator. It is not a quality score, efficiency measure, clinical outcome or
patient-satisfaction metric.

### Access-gap view

For each district and mandal in scope:

- `No active facility` when no active facility exists.
- `No active PHC/CHC/hospital` when active facilities exist but none map to primary care or higher.
- `Covered` otherwise.

This view does not account for travel time, transport, population need, service quality, staffing or actual
availability.

### Operational alerts

Alerts are generated from inactive facilities, overdue follow-ups, staffing gaps, pending reports, laboratory
awaiting review, pending screening review, pending verification, access gaps and spare capacity. Severity levels
are High, Medium and Info.

### Reporting and exports

The Reports module provides 12 CSV datasets:

1. Facilities
2. Service utilisation
3. Staffing gaps
4. Workforce
5. Screenings
6. Referrals
7. Diagnostics
8. Campaigns
9. Notifications
10. Substance-use cases
11. Employment applications
12. Appointments

A combined ZIP export includes every non-empty dataset. Files are generated in a temporary directory and contain
synthetic records only.

---

## 8. Service layer contracts

UI callbacks contain no SQL. Each callback opens a transactional session and calls a service function.

### `facility_service`

- Scope and discovery: `filtered_facility_ids`, `search_facilities`, `get_facility`, `facility_choices`,
  `facility_service_names`, `category_of`, `category_types`.
- Maintenance: `create_facility`, `update_facility`, `add_service`.
- Analytics: `utilization_rows`, `facility_count_by_type`, `referral_load_by_facility`,
  `service_availability_matrix`.

### `screening_service`

- Programmes: `list_programmes`, `programme_choices`, `create_programme`.
- Events: `facility_event_choices`, `create_event`, `list_events`.
- Participants: `participant_choices`, `register_participant`.
- Observations and review: `record_screening`, `review_queue`, `all_screenings`, `review_screening`,
  `pending_review_count`.

### `referral_service`

- Creation: `create_referral` with urgent-destination safety validation.
- Transitions: `transition_referral` against `REFERRAL_TRANSITIONS`.
- Queues and metrics: `list_referrals`, `overdue_count`, `open_count`, `referral_status_distribution`.

### `lab_service`

- Queue: `list_orders`, `order_choices`, `next_status`, `advance_order`.
- Report workflow: `enter_result`, `mark_result_available`, `verify_report`, `mark_reviewed`, `deliver_report`.
- Metrics: `awaiting_review_count`, `pending_report_count`, `report_status_distribution`,
  `orders_for_participant`.

### `reporting_service`

- Scope: `scope_ids`, `scope_label`.
- KPIs: `overview_kpis`, `dashboard_kpis`, `reports_summary`.
- Alerts and gaps: `operational_alerts`, `access_gap_rows`.
- Dataframes: facility type, screening by month, referral status, utilisation, staffing gap, service demand,
  service availability, facilities, screenings, referrals, staff, vacancies, applications, campaigns,
  notifications, substance-use cases, appointments and diagnostics.
- Exports: `export_csv`.
- Transition helper: `referral_transition_options`.

### `workforce_service`

- Staff: `list_staff`, `workforce_summary`, `facility_staffing_rows`.
- Vacancies: `list_vacancies`, `vacancy_choices`, `create_vacancy`, `update_vacancy`.
- Applications: `list_applications`, `create_application`, `update_application_status`.

### `notification_service`

- Campaigns: `list_campaigns`, `create_campaign`, `update_campaign_status`, `campaign_choices`.
- Notifications: `list_notifications`, `create_notification`, `update_notification_status`,
  `notification_choices`.
- Summary: `communication_summary`, `facility_names`.

### `substance_service`

- `list_cases`, `case_choices`, `create_case`, `update_case`, `summary`, `substance_distribution`,
  `cases_for_participant`.

### `citizen_service`

- Profiles: `participant_choices`, `get_participant`, `register_citizen`, `citizen_profile`, `citizen_summary`.
- Reminders and records: `reminders`, `health_records`, `referral_records`, `lab_records`, `all_records`.
- Discovery: `facility_options`, `service_options_for_facility`, `awareness_feed`, `citizen_notifications`.
- Appointments: `create_appointment`, `list_appointments`, `appointment_choices`, `update_appointment`,
  `cancel_appointment`.

### `ai_service`

Optional and disabled by default. Functions provide facility navigation guidance, administrative summaries,
campaign drafts and FAQ-style answers. When no provider is configured, deterministic fallbacks are returned. The
adapter is not used for diagnosis, prescribing or autonomous decisions.

### Error handling

Service functions raise `ValueError` for user-correctable validation failures. UI callbacks catch exceptions,
return a visible message and avoid partial writes by relying on transactional rollback. Tests assert the key safety
and workflow rules.

---

## 9. Safety, privacy and governance

### Clinical safety

1. Screening observations are not diagnoses and require qualified clinician review.
2. Urgent referrals are rejected unless the destination is emergency-capable.
3. Laboratory screens show workflow status only; no clinical values are fabricated.
4. No module provides diagnosis, prescribing, treatment planning or image interpretation.
5. Emergency guidance instructs users to seek immediate emergency care; the application is not an emergency
   service.

### Data privacy

1. All records are synthetic; participant identifiers are codes and aliases.
2. No Aadhaar, ABHA, real phone number, address or clinical record is stored.
3. The registry and portal expose limited operational information only.
4. Citizen registration and substance-use cases require recorded consent.
5. Substance-use data is confidential, voluntary and non-punitive and must not support enforcement or employment
   decisions.
6. Exports contain synthetic data and are written to temporary local storage.
7. The demo database is not encrypted and is unsuitable for real data.

### Communications

1. Campaigns and notifications are drafts or simulated; no external provider is called.
2. Campaign content requires human review and approval.
3. Appointment requests are not confirmed bookings.
4. No contact preference triggers a real message.

### AI governance

1. The AI adapter is disabled by default and requires explicit configuration.
2. It is limited to administrative and navigation support with deterministic fallbacks.
3. It must not be used for diagnosis, triage, prescribing or autonomous action.
4. Any production use would require approved providers, redaction, evaluation, logging and human approval.

### Access control

The role switcher is a demonstration control. It is not authentication and does not enforce permissions.
Production use requires an identity provider, MFA, scoped authorization, session management and audit retention.

---

## 10. Architecture, configuration and deployment

### Architecture

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

- `app.py` bootstraps the schema and seed data, builds the Blocks layout and wires navigation and role events.
- `src/ui` contains one module per screen plus shared components and theme.
- `src/services` contains all business logic, validation, workflow rules and derived metrics.
- `src/models` contains SQLAlchemy mappings split by domain.
- `src/seed.py` contains the deterministic synthetic dataset and reset logic.
- `src/database.py` owns the engine, transactional session scope and schema creation.

### Startup sequence

1. `bootstrap()` calls `init_db()` to create missing tables.
2. `seed_database(session)` inserts the deterministic dataset if the database is empty.
3. `build_app()` constructs the Gradio Blocks interface.
4. `main()` binds to `BHDC_SERVER_NAME` and the platform `PORT`.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BHDC_DB_PATH` | `data/bharat_health.db` | SQLite database path |
| `BHDC_SERVER_NAME` | `0.0.0.0` | Bind address |
| `BHDC_SERVER_PORT` / `PORT` | `7860` | Bind port |
| `BHDC_AI_ENABLED` | `0` | Enables optional AI adapter |
| `BHDC_AI_API_KEY` | empty | Provider key (never commit) |
| `BHDC_AI_MODEL` | `opencode/big-pickle` | Optional model label |

If `data/` is not writable, the application falls back to a temporary data directory. No secret is required for
core workflows.

### Hugging Face Spaces

The repository is configured for the Gradio SDK:

- Root `app.py` entry point.
- Pinned runtime dependencies in `requirements.txt`.
- README frontmatter declares `sdk: gradio`, `sdk_version: 5.50.0`, `app_file: app.py`, `python_version: 3.10`.
- The app binds to `0.0.0.0` and reads the platform port.
- SQLite is created and seeded automatically.

Spaces storage is ephemeral unless a persistent volume is attached. Demo edits may be lost on restart, and the seed
restores a clean baseline. Do not deploy real data or secrets to a public Space.

### Local development

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

For tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

---

## 11. Testing and quality

The test suite uses an isolated temporary SQLite database. `conftest.py` sets `BHDC_DB_PATH`, deletes the test
database at import and resets the deterministic dataset before each test.

Current status: **32 tests passing**.

| Test file | Coverage |
|---|---|
| `test_seed.py` | Deterministic counts and idempotent seeding |
| `test_facilities.py` | Service/mandal/type search, scoped filters, creation validation, utilisation formula fields |
| `test_screening.py` | Screening recording, clinician review, double-review rejection |
| `test_referrals.py` | Full lifecycle, invalid transitions, urgent-destination safety, overdue detection |
| `test_lab.py` | Workflow advancement, result entry, review requirement, delivery |
| `test_workforce.py` | Workforce summary, vacancy creation/filling, application workflow |
| `test_citizen.py` | Consent requirement, appointment lifecycle, invalid booking rejection |
| `test_operations.py` | Substance-use consent and confidentiality, status validation, simulated communications |
| `test_reports.py` | KPI consistency, district scoping, CSV export, reset, percentage calculations |

### Quality practices

- UI callbacks contain no SQL.
- Service functions raise explicit validation errors.
- Safety rules are covered by tests (urgent referrals, consent, review ordering).
- Seeds are deterministic and resettable.
- No external API is required for tests or core workflows.
- Charts render empty-state figures when scope has no matching data.

### Manual verification

- Build the interface: `from app import build_app; build_app()`.
- Launch locally and confirm the default Healthcare Overview, role switching and all 17 screen selections.
- Exercise one create/update path per domain and reset the dataset afterward.
- Verify that simulated-data, demo-role, screening, laboratory and emergency notices remain visible.

---

## 12. Operations and demo reset

### Resetting the demo

Use **Administration and Settings → Restore deterministic demo dataset** and type `RESET` to confirm. This removes
current demo edits and recreates the seed.

For a clean local schema after model changes:

```bash
rm -f data/bharat_health.db
python app.py
```

The application has no migration framework. Schema changes require recreating the local demo database or adding a
migration tool.

### Database and exports

- Default database: `data/bharat_health.db`.
- Test database: `/tmp/bhd_test.db`.
- CSV and ZIP exports are written to temporary directories and are not retained by the application.
- Spaces containers are ephemeral; attach a persistent volume only if demo persistence is required.

### Logs

Gradio logs appear on standard output. The launch call enables `show_error=True` for development support. Do not
log real data in any future deployment.

---

## 13. Scalability roadmap

| Area | Current prototype | Scalable next step |
|---|---|---|
| Identity | Demo role switcher | OIDC identity provider, MFA, scoped RBAC/ABAC |
| Database | SQLite file | Managed PostgreSQL with migrations, backups and row-level controls |
| Facility registry | Seeded demo directory | Verified registry with ownership and update workflow |
| Availability | Static notes | Facility-reported or integrated availability |
| Screening | Manual observation entry | Approved protocols, validated instruments, consent capture and clinical governance |
| Referrals | Local state machine | Cross-facility referral service with SLA tracking and notifications |
| Laboratory | Status-only workflow | LIS integration with authenticated results and audit |
| Workforce | Demo roster and vacancies | HR system integration and credential verification |
| Communications | Simulated drafts | Approved templates, consent, opt-out and delivery provider |
| Citizen portal | Synthetic profiles and requests | Verified identity, consent manager and confirmed booking integration |
| Reporting | Local CSV and ZIP | Versioned reporting pipeline, scheduled exports and dashboards |
| Interoperability | None | ABDM/ABHA sandbox with consent manager and standards-based exchange |
| AI | Optional adapter with fallbacks | Governed inference with redaction, evaluation, logging and human approval |
| Operations | Single process | Containers, health checks, monitoring, tracing and incident response |
| Security | Prototype notices | Encryption, secrets management, dependency scanning and penetration testing |

Adoption should be phased. A real pilot requires clinical governance, privacy review, security assessment,
accessibility review, user research, baseline measurement and an evaluation protocol.

---

## 14. Known limitations

- Role switching is not authentication and provides no real access control.
- All data is fictional and local; there is no multi-tenancy, encryption-at-rest or retention policy.
- No migrations; schema changes require recreating the demo database.
- Facility availability is not live and must be confirmed directly.
- Notifications and campaigns are simulated; nothing is sent.
- Appointment requests are not confirmed bookings.
- No ABDM/ABHA, HMIS, eSanjeevani, laboratory, pharmacy, payment or entitlement integration.
- No clinical decision support, diagnosis, prescribing or treatment planning.
- Utilisation, coverage, access-gap and completion metrics are illustrative planning indicators, not measured
  impact.
- SQLite is unsuitable for concurrent production use.
- The optional AI adapter is off by default and unsuited to clinical use.
- Some Gradio 5.50 theme and CSS constructor warnings are emitted at startup; they do not affect functionality.

---

## 15. Glossary

| Term | Meaning |
|---|---|
| AAM | Ayushman Arogya Mandir / Health & Wellness Centre |
| ABDM / ABHA | Ayushman Bharat Digital Mission / Health Account identifier |
| CHC | Community Health Centre |
| HMIS | Health Management Information System |
| LIS | Laboratory Information System |
| Mandal | Administrative sub-district unit used in the demo geography |
| PHC | Primary Health Centre |
| RBAC / ABAC | Role-based / attribute-based access control |
| Screening observation | A recorded screening finding requiring clinician review; not a diagnosis |
| Utilisation indicator | Demo attendance/capacity planning ratio; not a clinical quality score |
| Referral | A recorded request to move a participant to another facility for further care |
| Synthetic data | Fictional records created for demonstration and testing |

---

**License:** MIT. See `LICENSE` for details.
