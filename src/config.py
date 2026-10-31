"""Application configuration for the Bharat Health Detective Care platform.

All values are demo-safe. No secrets or real health data belong in this file.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _writable_data_dir() -> Path:
    """Prefer ./data; fall back to a temp dir on read-only hosting filesystems."""
    preferred = BASE_DIR / "data"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return preferred
    except OSError:
        import tempfile

        fallback = Path(tempfile.gettempdir()) / "bhd_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DATA_DIR = _writable_data_dir()

APP_NAME = "Bharat Health Detective Care"
APP_TAGLINE = "Detect Early. Care Locally. Protect Every Life."
DISTRICT = "Yadadri Bhuvanagiri (illustrative)"
DB_PATH = Path(os.getenv("BHDC_DB_PATH", str(DATA_DIR / "bharat_health.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

SIMULATED_BANNER = (
    "SIMULATED DATA — NOT FOR CLINICAL USE. All facilities, people and records "
    "in this prototype are fictional demonstration data."
)
ROLE_BANNER = "Demo role mode — not secure authentication."

# ---------------------------------------------------------------------------
# Geography (illustrative demo geography only)
# ---------------------------------------------------------------------------
STATE = "Telangana (illustrative)"
STATES = [STATE]
DISTRICTS = ["Yadadri Bhuvanagiri", "Nalgonda", "Medchal-Malkajgiri"]
MANDALS_BY_DISTRICT = {
    "Yadadri Bhuvanagiri": [
        "Bhuvanagiri", "Bommalaramaram", "Choutuppal", "Ramannapet", "Yadagirigutta", "Alair",
    ],
    "Nalgonda": ["Nalgonda", "Miryalaguda", "Nidamanoor"],
    "Medchal-Malkajgiri": ["Medchal", "Keesara", "Shamirpet"],
}
MANDALS = [m for group in MANDALS_BY_DISTRICT.values() for m in group]

# ---------------------------------------------------------------------------
# Roles and navigation
# ---------------------------------------------------------------------------
DEMO_ROLES = [
    "District Administrator",
    "State Health Administrator",
    "District Medical Officer",
    "Facility Administrator",
    "Medical Officer",
    "Laboratory Administrator",
    "Community Health Worker",
    "Citizen",
]

# ---------------------------------------------------------------------------
# Facility taxonomy
# ---------------------------------------------------------------------------
FACILITY_TYPES = [
    "Anganwadi / Child Development Centre",
    "Sub-centre",
    "Ayushman Arogya Mandir / Health & Wellness Centre",
    "PHC",
    "CHC",
    "District Hospital",
    "Medical College Hospital",
    "Government Laboratory",
    "Private Hospital / Lab (participating)",
]

FACILITY_CATEGORY_MAP = {
    "Anganwadi / Child Development Centre": "Community",
    "Sub-centre": "Community",
    "Ayushman Arogya Mandir / Health & Wellness Centre": "Community",
    "PHC": "Primary care",
    "CHC": "Secondary care",
    "District Hospital": "Tertiary care",
    "Medical College Hospital": "Tertiary care",
    "Government Laboratory": "Diagnostics",
    "Private Hospital / Lab (participating)": "Diagnostics / private",
}
FACILITY_CATEGORIES = ["Community", "Primary care", "Secondary care", "Tertiary care", "Diagnostics", "Diagnostics / private"]
FACILITY_CATEGORY_LABEL = "Facility category"
OWNERSHIP_TYPES = ["Government", "Local body", "Participating private", "Trust / NGO"]

VERIFICATION_STATUSES = ["Verified", "Pending verification", "Call to verify"]
OPERATING_STATUSES = ["Operational", "Partial services", "Temporarily closed"]
FACILITY_ACTIVE_OPTIONS = ["Active", "Inactive"]

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
SERVICE_CATEGORIES = [
    "Emergency", "General", "Preventive", "Diagnostics", "Maternal", "Child",
    "Specialist", "Pharmacy", "Rehabilitation", "Mental health", "Counselling",
]
SERVICE_OPTIONS = [
    "Emergency care", "General medicine", "NCD screening", "Laboratory diagnostics",
    "Maternal health", "Child health", "Vision screening", "Wellness counselling",
    "Ophthalmology", "Nutrition counselling", "Immunization", "Pharmacy",
    "Physiotherapy", "Mental health counselling", "Substance-use counselling",
    "Tuberculosis care", "Dental care", "Imaging / radiology",
]

# ---------------------------------------------------------------------------
# Workforce and employment
# ---------------------------------------------------------------------------
WORKFORCE_ROLES = [
    "Medical Officer", "Specialist Doctor", "Staff Nurse", "Auxiliary Nurse Midwife",
    "Lab Technician", "Pharmacist", "Physiotherapist", "Community Health Worker",
    "Facility Administrator", "Public Health Manager",
]
STAFF_AVAILABILITY = ["Available", "On duty", "On leave", "Unavailable"]
STAFF_SHIFTS = ["Day", "Night", "Rotational", "Field"]
VERIFICATION_OPTIONS = ["Verified", "Pending verification", "Call to verify"]
VACANCY_STATUSES = ["Open", "Partially filled", "Filled", "On hold"]
VACANCY_PRIORITIES = ["High", "Routine"]
APPLICATION_STATUSES = ["Received", "Shortlisted", "Interview scheduled", "Offer", "Rejected", "Withdrawn"]

# ---------------------------------------------------------------------------
# Screening, diagnostics, referrals
# ---------------------------------------------------------------------------
RESULT_CATEGORIES = ["Normal", "Needs clinician review", "Urgent review"]
SCREENING_REVIEW_STATUSES = ["Pending clinician review", "Reviewed", "Returned for clarification"]
LAB_FLOW = [
    "Ordered",
    "Sample collected",
    "Received by lab",
    "Processing",
    "Result available",
    "Clinician reviewed",
]
REPORT_STATUSES = ["Pending result entry", "Result entered", "Verified", "Delivered"]
LAB_PRIORITIES = ["Routine", "Urgent"]

REFERRAL_STATUSES = [
    "Draft", "Sent", "Accepted", "Scheduled", "Attended", "Completed",
    "Returned for clarification", "Cancelled",
]
REFERRAL_TRANSITIONS = {
    "Draft": {"Sent", "Cancelled"},
    "Sent": {"Accepted", "Returned for clarification", "Cancelled"},
    "Accepted": {"Scheduled", "Cancelled"},
    "Scheduled": {"Attended", "Cancelled", "Returned for clarification"},
    "Attended": {"Completed"},
    "Completed": set(),
    "Returned for clarification": {"Sent", "Cancelled"},
    "Cancelled": set(),
}
REFERRAL_PRIORITIES = ["Routine", "Urgent"]

# ---------------------------------------------------------------------------
# Campaigns, notifications, substance-use, appointments
# ---------------------------------------------------------------------------
CAMPAIGN_CHANNELS = ["Planned SMS", "Planned voice call", "Planned WhatsApp", "Community session", "Print / wall poster"]
CAMPAIGN_STATUSES = ["Draft", "Needs review", "Approved draft", "Scheduled (simulated)"]
NOTIFICATION_CHANNELS = ["Planned SMS", "Planned voice call", "Planned WhatsApp", "Notice board"]
NOTIFICATION_STATUSES = ["Draft", "Approved", "Simulated — sent", "Cancelled"]
SUBSTANCE_STATUSES = ["Screening recorded", "Counselling scheduled", "Counselling completed", "Referred", "Closed"]
APPOINTMENT_STATUSES = ["Requested", "Confirmed", "Attended", "Cancelled", "Missed"]

# ---------------------------------------------------------------------------
# AI adapter (optional, disabled by default)
# ---------------------------------------------------------------------------
AI_ENABLED = bool(os.getenv("BHDC_AI_API_KEY")) and os.getenv("BHDC_AI_ENABLED", "0") == "1"
AI_MODEL = os.getenv("BHDC_AI_MODEL", "opencode/big-pickle")
