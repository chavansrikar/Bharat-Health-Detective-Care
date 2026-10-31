"""Deterministic synthetic seed data for the enterprise prototype.

Every record is fictional. The dataset never contains real patient
identifiers, Aadhaar/ABHA IDs or phone numbers.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.models import (
    Appointment,
    AuditEvent,
    Campaign,
    EmploymentApplication,
    Facility,
    LabOrder,
    Notification,
    Participant,
    Programme,
    Referral,
    Screening,
    ScreeningEvent,
    Service,
    Staff,
    StaffVacancy,
    SubstanceUseCase,
)

TODAY = date.today()


def _d(days_ago: int) -> date:
    return TODAY - timedelta(days=days_ago)


def _dt(days_from_now: int, hour: int = 10) -> datetime:
    base = datetime.now(timezone.utc) + timedelta(days=days_from_now)
    return base.replace(hour=hour, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Facilities: code, name, type, district, mandal, locality, lat, lon, address,
# verification, operating, is_active, ownership, beds, catchment, capacity
# ---------------------------------------------------------------------------
FACILITIES = [
    # Yadadri Bhuvanagiri
    ("DH-01", "District Hospital, Bhuvanagiri", "District Hospital", "Yadadri Bhuvanagiri", "Bhuvanagiri", "Bhuvanagiri Town", 17.5120, 78.8870, "Hospital Road, Bhuvanagiri", "Verified", "Operational", True, "Government", 180, 450000, "180 beds; 24x7 emergency"),
    ("MCH-01", "Medical College Hospital (illustrative)", "Medical College Hospital", "Yadadri Bhuvanagiri", "Bhuvanagiri", "Raigiri Road", 17.5300, 78.8600, "Raigiri Road, Bhuvanagiri", "Pending verification", "Operational", True, "Government", 500, 700000, "Teaching hospital; specialist OPD"),
    ("CHC-BH-01", "Community Health Centre, Bhuvanagiri", "CHC", "Yadadri Bhuvanagiri", "Bhuvanagiri", "Bhuvanagiri Town", 17.5080, 78.8910, "Near bus stand, Bhuvanagiri", "Verified", "Operational", True, "Government", 30, 180000, "30 beds; lab and referral desk"),
    ("PHC-BH-01", "Primary Health Centre, Bhuvanagiri", "PHC", "Yadadri Bhuvanagiri", "Bhuvanagiri", "Bhuvanagiri Rural", 17.4950, 78.9020, "Rural ring road, Bhuvanagiri", "Verified", "Operational", True, "Government", 6, 60000, "6 beds; outpatient services"),
    ("AAM-BH-01", "Ayushman Arogya Mandir, Bhuvanagiri", "Ayushman Arogya Mandir / Health & Wellness Centre", "Yadadri Bhuvanagiri", "Bhuvanagiri", "Bhuvanagiri Ward 7", 17.5150, 78.8950, "Ward 7, Bhuvanagiri", "Verified", "Operational", True, "Government", 0, 30000, "Preventive and wellness services"),
    ("SC-BH-01", "Sub-centre, Bhuvanagiri East", "Sub-centre", "Yadadri Bhuvanagiri", "Bhuvanagiri", "East Colony", 17.5010, 78.9100, "East Colony, Bhuvanagiri", "Call to verify", "Partial services", True, "Government", 0, 12000, "Maternal and child services"),
    ("AW-BH-01", "Anganwadi Centre, Bhuvanagiri", "Anganwadi / Child Development Centre", "Yadadri Bhuvanagiri", "Bhuvanagiri", "Ward 3", 17.5090, 78.8840, "Ward 3, Bhuvanagiri", "Verified", "Operational", True, "Local body", 0, 8000, "Community service listing only"),
    ("PHC-BR-01", "Primary Health Centre, Bommalaramaram", "PHC", "Yadadri Bhuvanagiri", "Bommalaramaram", "Bommalaramaram", 17.5630, 78.8100, "Main road, Bommalaramaram", "Verified", "Operational", True, "Government", 6, 55000, "6 beds; NCD clinic"),
    ("AAM-BR-01", "Ayushman Arogya Mandir, Bommalaramaram", "Ayushman Arogya Mandir / Health & Wellness Centre", "Yadadri Bhuvanagiri", "Bommalaramaram", "Bommalaramaram", 17.5660, 78.8150, "Market road, Bommalaramaram", "Pending verification", "Operational", True, "Government", 0, 25000, "Wellness and screening"),
    ("CHC-CH-01", "Community Health Centre, Choutuppal", "CHC", "Yadadri Bhuvanagiri", "Choutuppal", "Choutuppal Town", 17.4520, 78.9200, "NH-65 service road, Choutuppal", "Verified", "Operational", True, "Government", 30, 190000, "30 beds; emergency and diagnostics"),
    ("PHC-CH-01", "Primary Health Centre, Choutuppal", "PHC", "Yadadri Bhuvanagiri", "Choutuppal", "Choutuppal Rural", 17.4400, 78.9350, "Rural block, Choutuppal", "Verified", "Temporarily closed", False, "Government", 6, 40000, "Outpatient; lab limited"),
    ("PVT-CH-01", "Participating Private Hospital, Choutuppal", "Private Hospital / Lab (participating)", "Yadadri Bhuvanagiri", "Choutuppal", "Choutuppal Town", 17.4480, 78.9250, "Bypass road, Choutuppal", "Pending verification", "Operational", True, "Participating private", 40, 120000, "40 beds; participating in demo network"),
    ("PHC-RM-01", "Primary Health Centre, Ramannapet", "PHC", "Yadadri Bhuvanagiri", "Ramannapet", "Ramannapet Town", 17.3800, 78.8700, "Station road, Ramannapet", "Verified", "Operational", True, "Government", 6, 52000, "6 beds; maternal health"),
    ("SC-RM-01", "Sub-centre, Ramannapet West", "Sub-centre", "Yadadri Bhuvanagiri", "Ramannapet", "West Colony", 17.3750, 78.8600, "West Colony, Ramannapet", "Call to verify", "Operational", True, "Government", 0, 10000, "Maternal and child services"),
    ("AW-RM-01", "Anganwadi Centre, Ramannapet", "Anganwadi / Child Development Centre", "Yadadri Bhuvanagiri", "Ramannapet", "Ramannapet", 17.3820, 78.8760, "Ramannapet", "Verified", "Operational", True, "Local body", 0, 7000, "Community service listing only"),
    ("CHC-YG-01", "Community Health Centre, Yadagirigutta", "CHC", "Yadadri Bhuvanagiri", "Yadagirigutta", "Yadagirigutta Town", 17.5900, 78.9400, "Temple road, Yadagirigutta", "Verified", "Operational", True, "Government", 30, 175000, "30 beds; high pilgrim footfall"),
    ("AAM-YG-01", "Ayushman Arogya Mandir, Yadagirigutta", "Ayushman Arogya Mandir / Health & Wellness Centre", "Yadadri Bhuvanagiri", "Yadagirigutta", "Yadagirigutta", 17.5930, 78.9450, "Near bus station, Yadagirigutta", "Verified", "Operational", True, "Government", 0, 28000, "Wellness and NCD screening"),
    ("PHC-AL-01", "Primary Health Centre, Alair", "PHC", "Yadadri Bhuvanagiri", "Alair", "Alair Town", 17.6300, 79.0400, "Highway road, Alair", "Verified", "Operational", True, "Government", 6, 58000, "6 beds; outpatient"),
    ("LAB-GOV-01", "Government Laboratory, Bhuvanagiri", "Government Laboratory", "Yadadri Bhuvanagiri", "Bhuvanagiri", "Bhuvanagiri Town", 17.5110, 78.8890, "District hospital campus", "Verified", "Operational", True, "Government", 0, 0, "Sample collection and processing"),
    ("LAB-PVT-01", "Participating Private Lab, Choutuppal", "Private Hospital / Lab (participating)", "Yadadri Bhuvanagiri", "Choutuppal", "Choutuppal Town", 17.4490, 78.9270, "Bypass road, Choutuppal", "Pending verification", "Operational", True, "Participating private", 0, 0, "Participating diagnostics"),
    # Nalgonda (illustrative)
    ("DH-NL-01", "District Hospital, Nalgonda", "District Hospital", "Nalgonda", "Nalgonda", "Nalgonda Town", 17.0570, 79.2680, "Hospital road, Nalgonda", "Verified", "Operational", True, "Government", 160, 420000, "160 beds; 24x7 emergency"),
    ("CHC-NL-01", "Community Health Centre, Miryalaguda", "CHC", "Nalgonda", "Miryalaguda", "Miryalaguda", 16.8730, 79.5680, "Central road, Miryalaguda", "Verified", "Operational", True, "Government", 30, 160000, "30 beds; lab and referral desk"),
    ("PHC-NL-01", "Primary Health Centre, Nalgonda", "PHC", "Nalgonda", "Nalgonda", "Nalgonda Rural", 17.0500, 79.2800, "Rural block, Nalgonda", "Verified", "Operational", True, "Government", 6, 48000, "6 beds; outpatient"),
    ("AAM-NL-01", "Ayushman Arogya Mandir, Nalgonda", "Ayushman Arogya Mandir / Health & Wellness Centre", "Nalgonda", "Nalgonda", "Nalgonda Ward 4", 17.0600, 79.2700, "Ward 4, Nalgonda", "Pending verification", "Partial services", True, "Government", 0, 26000, "Wellness and screening"),
    ("LAB-NL-01", "Government Laboratory, Nalgonda", "Government Laboratory", "Nalgonda", "Nalgonda", "Nalgonda Town", 17.0580, 79.2650, "District hospital campus", "Verified", "Operational", True, "Government", 0, 0, "Sample processing"),
    # Medchal-Malkajgiri (illustrative)
    ("DH-MD-01", "District Hospital, Medchal", "District Hospital", "Medchal-Malkajgiri", "Medchal", "Medchal Town", 17.6290, 78.4810, "Main road, Medchal", "Verified", "Operational", True, "Government", 140, 380000, "140 beds; emergency and specialist OPD"),
    ("CHC-MD-01", "Community Health Centre, Keesara", "CHC", "Medchal-Malkajgiri", "Keesara", "Keesara", 17.5200, 78.6100, "Keesara main road", "Verified", "Operational", True, "Government", 30, 150000, "30 beds; emergency and diagnostics"),
    ("PHC-MD-01", "Primary Health Centre, Shamirpet", "PHC", "Medchal-Malkajgiri", "Shamirpet", "Shamirpet", 17.6100, 78.5700, "Shamirpet road", "Verified", "Operational", True, "Government", 6, 50000, "6 beds; outpatient"),
    ("AAM-MD-01", "Ayushman Arogya Mandir, Medchal", "Ayushman Arogya Mandir / Health & Wellness Centre", "Medchal-Malkajgiri", "Medchal", "Medchal", 17.6300, 78.4850, "Medchal market road", "Verified", "Operational", True, "Government", 0, 24000, "Wellness and vision screening"),
    ("LAB-MD-01", "Government Laboratory, Medchal", "Government Laboratory", "Medchal-Malkajgiri", "Medchal", "Medchal Town", 17.6280, 78.4830, "District hospital campus", "Verified", "Operational", True, "Government", 0, 0, "Sample processing"),
]

SERVICE_MAP = {
    "DH-01": [("Emergency care", "Emergency", 240, "24x7 emergency department"),
              ("General medicine", "General", 180, "Daily OPD"),
              ("NCD screening", "Preventive", 120, "BP and sugar screening"),
              ("Laboratory diagnostics", "Diagnostics", 150, "Sample collection daily"),
              ("Maternal health", "Maternal", 80, "ANC and delivery"),
              ("Ophthalmology", "Specialist", 60, "Weekly eye clinic"),
              ("Physiotherapy", "Rehabilitation", 40, "Weekday sessions"),
              ("Pharmacy", "Pharmacy", 200, "24x7 pharmacy")],
    "MCH-01": [("Specialist OPD", "Specialist", 150, "Referral-based specialist care"),
               ("Emergency care", "Emergency", 120, "Emergency department"),
               ("Laboratory diagnostics", "Diagnostics", 120, "Advanced diagnostics"),
               ("Imaging / radiology", "Diagnostics", 80, "Referral imaging")],
    "CHC-BH-01": [("Emergency care", "Emergency", 90, "Day and night emergency"),
                  ("NCD screening", "Preventive", 100, "NCD clinic weekdays"),
                  ("Laboratory diagnostics", "Diagnostics", 90, "Basic lab"),
                  ("Maternal health", "Maternal", 70, "ANC and safe delivery"),
                  ("Child health", "Child", 60, "Immunization and growth monitoring"),
                  ("Substance-use counselling", "Counselling", 30, "Confidential counselling"),
                  ("Pharmacy", "Pharmacy", 120, "OPD pharmacy")],
    "PHC-BH-01": [("General medicine", "General", 80, "Weekday OPD"),
                  ("NCD screening", "Preventive", 60, "BP and sugar screening"),
                  ("Maternal health", "Maternal", 40, "ANC services"),
                  ("Pharmacy", "Pharmacy", 60, "OPD pharmacy")],
    "AAM-BH-01": [("NCD screening", "Preventive", 90, "Community screening"),
                  ("Wellness counselling", "Preventive", 60, "Lifestyle counselling"),
                  ("Child health", "Child", 40, "Growth monitoring"),
                  ("Mental health counselling", "Mental health", 25, "Confidential counselling")],
    "SC-BH-01": [("Maternal health", "Maternal", 30, "ANC and postnatal visits"),
                 ("Child health", "Child", 30, "Immunization")],
    "AW-BH-01": [("Child health", "Child", 40, "Anganwadi services"),
                 ("Nutrition counselling", "Preventive", 30, "Community nutrition support")],
    "PHC-BR-01": [("General medicine", "General", 70, "Weekday OPD"),
                  ("NCD screening", "Preventive", 60, "NCD clinic"),
                  ("Laboratory diagnostics", "Diagnostics", 40, "Basic lab"),
                  ("Pharmacy", "Pharmacy", 50, "OPD pharmacy")],
    "AAM-BR-01": [("NCD screening", "Preventive", 70, "Community screening"),
                  ("Vision screening", "Preventive", 40, "Vision checks")],
    "CHC-CH-01": [("Emergency care", "Emergency", 100, "Emergency services"),
                  ("NCD screening", "Preventive", 90, "NCD clinic"),
                  ("Laboratory diagnostics", "Diagnostics", 100, "Lab and imaging referral"),
                  ("Maternal health", "Maternal", 60, "ANC and delivery"),
                  ("Pharmacy", "Pharmacy", 100, "OPD pharmacy")],
    "PHC-CH-01": [("General medicine", "General", 60, "Weekday OPD"),
                  ("NCD screening", "Preventive", 40, "Limited NCD clinic")],
    "PVT-CH-01": [("General medicine", "General", 80, "Participating private OPD"),
                  ("Laboratory diagnostics", "Diagnostics", 80, "Participating lab"),
                  ("Ophthalmology", "Specialist", 40, "Visiting specialist")],
    "PHC-RM-01": [("Maternal health", "Maternal", 60, "ANC and postnatal care"),
                  ("General medicine", "General", 60, "Weekday OPD"),
                  ("Child health", "Child", 50, "Immunization")],
    "SC-RM-01": [("Maternal health", "Maternal", 30, "ANC visits"),
                 ("Child health", "Child", 30, "Immunization")],
    "AW-RM-01": [("Child health", "Child", 35, "Anganwadi services"),
                 ("Nutrition counselling", "Preventive", 25, "Nutrition support")],
    "CHC-YG-01": [("Emergency care", "Emergency", 110, "Emergency services"),
                  ("General medicine", "General", 90, "OPD"),
                  ("NCD screening", "Preventive", 80, "NCD clinic"),
                  ("Laboratory diagnostics", "Diagnostics", 90, "Basic lab"),
                  ("Substance-use counselling", "Counselling", 25, "Confidential counselling")],
    "AAM-YG-01": [("NCD screening", "Preventive", 80, "Community screening"),
                  ("Wellness counselling", "Preventive", 50, "Lifestyle counselling")],
    "PHC-AL-01": [("General medicine", "General", 60, "Weekday OPD"),
                  ("NCD screening", "Preventive", 40, "NCD clinic"),
                  ("Pharmacy", "Pharmacy", 40, "OPD pharmacy")],
    "LAB-GOV-01": [("Laboratory diagnostics", "Diagnostics", 180, "Sample processing"),
                   ("NCD screening", "Preventive", 60, "Screening support")],
    "LAB-PVT-01": [("Laboratory diagnostics", "Diagnostics", 100, "Participating diagnostics")],
    "DH-NL-01": [("Emergency care", "Emergency", 200, "24x7 emergency"),
                 ("General medicine", "General", 150, "Daily OPD"),
                 ("NCD screening", "Preventive", 100, "NCD clinic"),
                 ("Laboratory diagnostics", "Diagnostics", 120, "Sample collection"),
                 ("Maternal health", "Maternal", 70, "ANC and delivery")],
    "CHC-NL-01": [("Emergency care", "Emergency", 80, "Emergency services"),
                  ("NCD screening", "Preventive", 80, "NCD clinic"),
                  ("Laboratory diagnostics", "Diagnostics", 80, "Basic lab"),
                  ("Child health", "Child", 50, "Immunization")],
    "PHC-NL-01": [("General medicine", "General", 60, "Weekday OPD"),
                  ("NCD screening", "Preventive", 40, "NCD clinic"),
                  ("Maternal health", "Maternal", 40, "ANC services")],
    "AAM-NL-01": [("NCD screening", "Preventive", 60, "Community screening"),
                  ("Wellness counselling", "Preventive", 40, "Lifestyle counselling")],
    "LAB-NL-01": [("Laboratory diagnostics", "Diagnostics", 120, "Sample processing")],
    "DH-MD-01": [("Emergency care", "Emergency", 180, "24x7 emergency"),
                 ("General medicine", "General", 130, "Daily OPD"),
                 ("NCD screening", "Preventive", 90, "NCD clinic"),
                 ("Laboratory diagnostics", "Diagnostics", 100, "Sample collection"),
                 ("Ophthalmology", "Specialist", 50, "Weekly eye clinic")],
    "CHC-MD-01": [("Emergency care", "Emergency", 90, "Emergency services"),
                  ("NCD screening", "Preventive", 80, "NCD clinic"),
                  ("Laboratory diagnostics", "Diagnostics", 80, "Basic lab")],
    "PHC-MD-01": [("General medicine", "General", 60, "Weekday OPD"),
                  ("NCD screening", "Preventive", 40, "NCD clinic")],
    "AAM-MD-01": [("NCD screening", "Preventive", 60, "Community screening"),
                  ("Vision screening", "Preventive", 35, "Vision checks")],
    "LAB-MD-01": [("Laboratory diagnostics", "Diagnostics", 110, "Sample processing")],
}

# (code, alias, age_band, gender, locality, district)
PARTICIPANTS = [
    ("P-0001", "Alias A01", "31-45", "Female", "Bhuvanagiri", "Yadadri Bhuvanagiri"),
    ("P-0002", "Alias A02", "46-60", "Male", "Bhuvanagiri", "Yadadri Bhuvanagiri"),
    ("P-0003", "Alias A03", "60+", "Female", "Bommalaramaram", "Yadadri Bhuvanagiri"),
    ("P-0004", "Alias A04", "18-30", "Female", "Choutuppal", "Yadadri Bhuvanagiri"),
    ("P-0005", "Alias A05", "31-45", "Female", "Ramannapet", "Yadadri Bhuvanagiri"),
    ("P-0006", "Alias A06", "46-60", "Male", "Yadagirigutta", "Yadadri Bhuvanagiri"),
    ("P-0007", "Alias A07", "60+", "Male", "Alair", "Yadadri Bhuvanagiri"),
    ("P-0008", "Alias A08", "0-5", "Female", "Bhuvanagiri", "Yadadri Bhuvanagiri"),
    ("P-0009", "Alias A09", "6-17", "Male", "Bommalaramaram", "Yadadri Bhuvanagiri"),
    ("P-0010", "Alias A10", "18-30", "Female", "Choutuppal", "Yadadri Bhuvanagiri"),
    ("P-0011", "Alias A11", "31-45", "Female", "Ramannapet", "Yadadri Bhuvanagiri"),
    ("P-0012", "Alias A12", "46-60", "Male", "Yadagirigutta", "Yadadri Bhuvanagiri"),
    ("P-0013", "Alias A13", "60+", "Female", "Bhuvanagiri", "Yadadri Bhuvanagiri"),
    ("P-0014", "Alias A14", "31-45", "Male", "Alair", "Yadadri Bhuvanagiri"),
    ("P-0015", "Alias A15", "18-30", "Female", "Bommalaramaram", "Yadadri Bhuvanagiri"),
    ("P-0016", "Alias A16", "46-60", "Female", "Choutuppal", "Yadadri Bhuvanagiri"),
    ("P-0017", "Alias A17", "60+", "Male", "Ramannapet", "Yadadri Bhuvanagiri"),
    ("P-0018", "Alias A18", "0-5", "Male", "Yadagirigutta", "Yadadri Bhuvanagiri"),
    ("P-0019", "Alias A19", "6-17", "Female", "Bhuvanagiri", "Yadadri Bhuvanagiri"),
    ("P-0020", "Alias A20", "31-45", "Male", "Alair", "Yadadri Bhuvanagiri"),
    ("P-0021", "Alias A21", "46-60", "Female", "Bhuvanagiri", "Yadadri Bhuvanagiri"),
    ("P-0022", "Alias A22", "18-30", "Male", "Bommalaramaram", "Yadadri Bhuvanagiri"),
    ("P-0023", "Alias A23", "60+", "Female", "Choutuppal", "Yadadri Bhuvanagiri"),
    ("P-0024", "Alias A24", "31-45", "Female", "Ramannapet", "Yadadri Bhuvanagiri"),
    ("P-0025", "Alias A25", "46-60", "Male", "Yadagirigutta", "Yadadri Bhuvanagiri"),
    ("P-0026", "Alias A26", "0-5", "Female", "Alair", "Yadadri Bhuvanagiri"),
    ("P-0027", "Alias A27", "6-17", "Male", "Bhuvanagiri", "Yadadri Bhuvanagiri"),
    ("P-0028", "Alias A28", "18-30", "Female", "Bommalaramaram", "Yadadri Bhuvanagiri"),
    ("P-0029", "Alias A29", "60+", "Male", "Choutuppal", "Yadadri Bhuvanagiri"),
    ("P-0030", "Alias A30", "31-45", "Female", "Ramannapet", "Yadadri Bhuvanagiri"),
    ("P-0031", "Alias A31", "31-45", "Female", "Nalgonda", "Nalgonda"),
    ("P-0032", "Alias A32", "46-60", "Male", "Miryalaguda", "Nalgonda"),
    ("P-0033", "Alias A33", "60+", "Female", "Nalgonda", "Nalgonda"),
    ("P-0034", "Alias A34", "18-30", "Male", "Medchal", "Medchal-Malkajgiri"),
    ("P-0035", "Alias A35", "31-45", "Female", "Keesara", "Medchal-Malkajgiri"),
    ("P-0036", "Alias A36", "46-60", "Female", "Shamirpet", "Medchal-Malkajgiri"),
    ("P-0037", "Alias A37", "6-17", "Male", "Medchal", "Medchal-Malkajgiri"),
    ("P-0038", "Alias A38", "0-5", "Female", "Nalgonda", "Nalgonda"),
    ("P-0039", "Alias A39", "60+", "Male", "Keesara", "Medchal-Malkajgiri"),
    ("P-0040", "Alias A40", "31-45", "Female", "Shamirpet", "Medchal-Malkajgiri"),
]

WORKERS = ["CHW Meena (alias)", "CHW Ravi (alias)", "CHW Lakshmi (alias)", "CHW Kumar (alias)",
           "CHW Padma (alias)", "CHW Sita (alias)"]

PROGRAMMES = [
    ("NCD Early Detection Programme", "Community blood-pressure and glucose screening with clinician review and referral.", "Adults 30+ in selected mandals", "Adults 30+; voluntary participation; confirm eligibility locally", "Illustrative protocol — confirm with local clinical authority", _d(180), _d(-30), "Active"),
    ("Maternal & Child Health Follow-up", "Track antenatal visits, immunization and growth monitoring in the demo network.", "Pregnant women and children under 5", "Voluntary participation; clinical eligibility confirmed at facility", "Illustrative protocol — confirm with local clinical authority", _d(150), _d(-60), "Active"),
    ("School Vision & Oral Health Screening", "School-based vision and oral health checks with referral coordination.", "Children aged 6-17 in selected schools", "School consent process required; opt-out respected", "Illustrative protocol — confirm with local clinical authority", _d(120), _d(-20), "Planned"),
    ("Adolescent Mental Health & Substance-Use Awareness", "Confidential, non-punitive awareness, screening and counselling linkage for adolescents and adults.", "Adolescents 13-19 and adults", "Voluntary and confidential; no punitive or enforcement use", "Illustrative guidance — confirm with local clinical authority", _d(90), _d(-90), "Active"),
]

# (code, name, role, qualification, facility_code, skills, availability, shift, employment_type)
STAFF = [
    ("S-001", "Dr. Rao (alias)", "Medical Officer", "MBBS (demo)", "CHC-BH-01", "NCD review, referral", "Available", "Day", "Regular"),
    ("S-002", "Dr. Iyer (alias)", "Medical Officer", "MBBS (demo)", "CHC-CH-01", "Maternal health", "On duty", "Day", "Regular"),
    ("S-003", "Dr. Fatima (alias)", "Medical Officer", "MBBS, DGO (demo)", "PHC-RM-01", "Maternal health, ANC", "Available", "Day", "Regular"),
    ("S-004", "Dr. Verma (alias)", "Medical Officer", "MBBS (demo)", "DH-01", "Emergency, general medicine", "On duty", "Night", "Regular"),
    ("S-005", "Nurse Anitha (alias)", "Staff Nurse", "GNM (demo)", "CHC-BH-01", "Screening, immunization", "Available", "Day", "Regular"),
    ("S-006", "Nurse Sunita (alias)", "Staff Nurse", "GNM (demo)", "PHC-BR-01", "NCD screening", "Available", "Day", "Contract"),
    ("S-007", "Tech Suresh (alias)", "Lab Technician", "DMLT (demo)", "LAB-GOV-01", "Sample collection", "Available", "Day", "Regular"),
    ("S-008", "Tech Priya (alias)", "Lab Technician", "DMLT (demo)", "LAB-PVT-01", "Sample processing", "Available", "Day", "Contract"),
    ("S-009", "CHW Meena (alias)", "Community Health Worker", "ASHA training (demo)", "AAM-BH-01", "Outreach, follow-up", "Available", "Field", "Honorary"),
    ("S-010", "CHW Ravi (alias)", "Community Health Worker", "ASHA training (demo)", "PHC-BR-01", "Outreach, follow-up", "Available", "Field", "Honorary"),
    ("S-011", "CHW Lakshmi (alias)", "Community Health Worker", "ASHA training (demo)", "PHC-RM-01", "Maternal follow-up", "On leave", "Field", "Honorary"),
    ("S-012", "Admin Kiran (alias)", "Facility Administrator", "MPH (demo)", "CHC-CH-01", "Operations, capacity", "Available", "Day", "Regular"),
    ("S-013", "Dr. Naidu (alias)", "Medical Officer", "MBBS (demo)", "DH-NL-01", "General medicine", "Available", "Day", "Regular"),
    ("S-014", "Nurse Bhavani (alias)", "Staff Nurse", "GNM (demo)", "CHC-NL-01", "Maternal health", "On duty", "Rotational", "Regular"),
    ("S-015", "Pharmacist Ramesh (alias)", "Pharmacist", "B.Pharm (demo)", "PHC-NL-01", "Dispensing", "Available", "Day", "Regular"),
    ("S-016", "Physio Divya (alias)", "Physiotherapist", "BPT (demo)", "DH-01", "Rehabilitation", "Available", "Day", "Contract"),
    ("S-017", "Dr. Sana (alias)", "Specialist Doctor", "MD (demo)", "DH-MD-01", "Ophthalmology", "On duty", "Day", "Regular"),
    ("S-018", "Nurse Keerthi (alias)", "Staff Nurse", "GNM (demo)", "CHC-MD-01", "Emergency, screening", "Available", "Night", "Regular"),
    ("S-019", "Tech Arun (alias)", "Lab Technician", "DMLT (demo)", "LAB-NL-01", "Sample processing", "Available", "Day", "Regular"),
    ("S-020", "CHW Padma (alias)", "Community Health Worker", "ASHA training (demo)", "AAM-NL-01", "Outreach, counselling linkage", "Available", "Field", "Honorary"),
    ("S-021", "Pharmacist Naveen (alias)", "Pharmacist", "B.Pharm (demo)", "PHC-MD-01", "Dispensing", "On leave", "Day", "Contract"),
    ("S-022", "Manager Ritu (alias)", "Public Health Manager", "MPH (demo)", "DH-MD-01", "Operations, analytics", "Available", "Day", "Regular"),
]

EVENTS = [
    ("EV-001", 0, "CHC-BH-01", "NCD screening camp — Bhuvanagiri", 150, "Completed", 118),
    ("EV-002", 1, "CHC-CH-01", "NCD screening camp — Choutuppal", 120, "Completed", 74),
    ("EV-003", 2, "CHC-YG-01", "Maternal health camp — Yadagirigutta", 90, "Completed", 61),
    ("EV-004", 1, "PHC-BR-01", "NCD screening camp — Bommalaramaram", 60, "Completed", 48),
    ("EV-005", 0, "AAM-BH-01", "Wellness screening — Bhuvanagiri", -12, "Planned", 0),
    ("EV-006", 0, "CHC-NL-01", "NCD screening camp — Miryalaguda", 40, "Completed", 56),
    ("EV-007", 2, "PHC-MD-01", "School vision screening — Shamirpet", 20, "Completed", 32),
]

SCREENINGS = [
    (0, 0, "Blood pressure", "BP recorded above demo threshold on two readings.", "Needs clinician review", "Pending clinician review"),
    (0, 1, "Blood pressure", "BP within demo reference range.", "Normal", "Reviewed"),
    (0, 12, "Random glucose", "Glucose above demo threshold; repeat advised.", "Needs clinician review", "Pending clinician review"),
    (0, 20, "Random glucose", "Glucose within demo reference range.", "Normal", "Reviewed"),
    (0, 26, "Vision", "Reduced vision reported on demo chart.", "Needs clinician review", "Pending clinician review"),
    (1, 3, "Blood pressure", "BP recorded above demo threshold.", "Urgent review", "Pending clinician review"),
    (1, 9, "Blood pressure", "BP within demo reference range.", "Normal", "Reviewed"),
    (1, 15, "Random glucose", "Glucose within demo reference range.", "Normal", "Reviewed"),
    (1, 22, "Random glucose", "Glucose above demo threshold; repeat advised.", "Needs clinician review", "Pending clinician review"),
    (1, 28, "Vision", "Vision within demo reference range.", "Normal", "Reviewed"),
    (2, 4, "Antenatal check", "ANC visit recorded; routine follow-up advised.", "Normal", "Reviewed"),
    (2, 5, "Antenatal check", "ANC visit recorded; routine follow-up advised.", "Normal", "Reviewed"),
    (2, 10, "Antenatal check", "ANC visit recorded; clinician review requested.", "Needs clinician review", "Pending clinician review"),
    (2, 16, "Antenatal check", "ANC visit recorded; routine follow-up advised.", "Normal", "Reviewed"),
    (2, 23, "Antenatal check", "ANC visit recorded; routine follow-up advised.", "Normal", "Reviewed"),
    (3, 2, "Blood pressure", "BP above demo threshold; referral for review.", "Urgent review", "Reviewed"),
    (3, 8, "Blood pressure", "BP within demo reference range.", "Normal", "Reviewed"),
    (3, 14, "Random glucose", "Glucose above demo threshold; repeat advised.", "Needs clinician review", "Pending clinician review"),
    (3, 21, "Vision", "Reduced vision reported on demo chart.", "Needs clinician review", "Reviewed"),
    (3, 27, "Vision", "Vision within demo reference range.", "Normal", "Reviewed"),
    (0, 6, "Blood pressure", "BP within demo reference range.", "Normal", "Reviewed"),
    (0, 13, "Random glucose", "Glucose above demo threshold; repeat advised.", "Needs clinician review", "Pending clinician review"),
    (1, 18, "Child growth", "Growth monitoring recorded; follow-up scheduled.", "Normal", "Reviewed"),
    (2, 24, "Child growth", "Growth monitoring recorded; clinician review requested.", "Needs clinician review", "Pending clinician review"),
    (5, 30, "Blood pressure", "BP above demo threshold; referral for review.", "Urgent review", "Pending clinician review"),
    (5, 31, "Random glucose", "Glucose above demo threshold; repeat advised.", "Needs clinician review", "Pending clinician review"),
    (5, 32, "Vision", "Reduced vision reported on demo chart.", "Needs clinician review", "Reviewed"),
    (6, 33, "Vision", "Vision within demo reference range.", "Normal", "Reviewed"),
    (6, 34, "Blood pressure", "BP within demo reference range.", "Normal", "Reviewed"),
    (6, 35, "Child growth", "Growth monitoring recorded; follow-up scheduled.", "Normal", "Reviewed"),
]

# (screening_index, source, destination, reason, priority, status, days_ago, note)
REFERRALS = [
    (0, "CHC-BH-01", "DH-01", "Elevated blood pressure — clinical review", "Urgent", "Scheduled", 2, ""),
    (2, "CHC-BH-01", "DH-01", "Elevated glucose — diagnostic confirmation", "Routine", "Sent", 5, ""),
    (5, "CHC-CH-01", "DH-01", "Urgent BP review — same-day assessment", "Urgent", "Accepted", 0, ""),
    (8, "CHC-CH-01", "PHC-CH-01", "Repeat glucose screening", "Routine", "Completed", 10, "Attended; follow-up advised."),
    (12, "CHC-YG-01", "PHC-RM-01", "Antenatal clinical review", "Routine", "Attended", 1, ""),
    (15, "PHC-BR-01", "CHC-CH-01", "Urgent BP review", "Urgent", "Completed", 12, "Reviewed and closed."),
    (17, "PHC-BR-01", "CHC-BH-01", "Glucose confirmatory testing", "Routine", "Sent", 4, ""),
    (18, "PHC-BR-01", "MCH-01", "Vision specialist review", "Routine", "Sent", 7, ""),
    (21, "AAM-BH-01", "CHC-BH-01", "Repeat glucose screening", "Routine", "Returned for clarification", 3, "Clarify participant contact preference."),
    (22, "CHC-CH-01", "PHC-CH-01", "Child growth clinical review", "Routine", "Draft", 6, ""),
    (23, "CHC-YG-01", "PHC-RM-01", "Child growth clinical review", "Routine", "Draft", 8, ""),
    (10, "CHC-YG-01", "CHC-CH-01", "Antenatal clinical review", "Urgent", "Cancelled", 0, "Participant requested reschedule."),
    (24, "CHC-NL-01", "DH-NL-01", "Urgent BP review — same-day assessment", "Urgent", "Sent", 3, ""),
    (25, "CHC-NL-01", "DH-NL-01", "Glucose confirmatory testing", "Routine", "Scheduled", 2, ""),
    (26, "PHC-MD-01", "CHC-MD-01", "Vision clinical review", "Routine", "Accepted", 4, ""),
    (27, "PHC-MD-01", "DH-MD-01", "Child growth clinical review", "Routine", "Completed", 9, "Reviewed and closed."),
]

LAB_SPECS = [
    (0, "LAB-GOV-01", "Blood pressure panel (demo)", "Routine", "Result available", "Awaiting clinician review", "Pending result entry"),
    (1, "LAB-GOV-01", "Glucose confirmatory (demo)", "Routine", "Processing", "Pending", "Pending result entry"),
    (2, "LAB-PVT-01", "Urgent BP panel (demo)", "Urgent", "Sample collected", "Pending", "Pending result entry"),
    (3, "LAB-PVT-01", "Repeat glucose (demo)", "Routine", "Result available", "Reviewed", "Delivered"),
    (4, "LAB-GOV-01", "Antenatal panel (demo)", "Routine", "Received by lab", "Pending", "Pending result entry"),
    (5, "LAB-GOV-01", "BP panel (demo)", "Routine", "Result available", "Reviewed", "Verified"),
    (6, "LAB-GOV-01", "Glucose confirmatory (demo)", "Routine", "Ordered", "Pending", "Pending result entry"),
    (7, "LAB-PVT-01", "Vision referral notes (demo)", "Routine", "Result available", "Awaiting clinician review", "Result entered"),
    (12, "LAB-NL-01", "Glucose confirmatory (demo)", "Routine", "Result available", "Awaiting clinician review", "Result entered"),
    (13, "LAB-NL-01", "BP panel (demo)", "Routine", "Processing", "Pending", "Pending result entry"),
    (14, "LAB-MD-01", "Vision referral notes (demo)", "Routine", "Sample collected", "Pending", "Pending result entry"),
    (15, "LAB-MD-01", "Child growth panel (demo)", "Routine", "Result available", "Reviewed", "Delivered"),
]

# (facility, role, required, filled, status, priority, notes)
VACANCIES = [
    ("CHC-BH-01", "Medical Officer", 4, 2, "Partially filled", "High", "Emergency and NCD cover"),
    ("PHC-BH-01", "Medical Officer", 2, 1, "Partially filled", "High", "Weekday OPD"),
    ("PHC-BR-01", "Staff Nurse", 4, 2, "Partially filled", "Routine", "Screening support"),
    ("PHC-RM-01", "Medical Officer", 2, 2, "Filled", "Routine", ""),
    ("CHC-YG-01", "Medical Officer", 4, 3, "Partially filled", "High", "Pilgrim season cover"),
    ("PHC-AL-01", "Medical Officer", 2, 0, "Open", "High", "No regular MO recorded"),
    ("AAM-BH-01", "Community Health Worker", 4, 3, "Partially filled", "Routine", "Outreach"),
    ("AAM-BR-01", "Community Health Worker", 3, 1, "Open", "Routine", "Rural outreach"),
    ("DH-01", "Specialist Doctor", 6, 4, "Partially filled", "High", "Specialist OPD"),
    ("DH-01", "Staff Nurse", 20, 16, "Partially filled", "Routine", "Shift coverage"),
    ("CHC-CH-01", "Lab Technician", 3, 2, "Partially filled", "Routine", "Lab workload"),
    ("LAB-GOV-01", "Lab Technician", 4, 3, "Partially filled", "High", "Sample backlog"),
    ("DH-NL-01", "Medical Officer", 5, 4, "Partially filled", "Routine", "Emergency cover"),
    ("CHC-NL-01", "Staff Nurse", 8, 5, "Partially filled", "High", "Maternal and emergency"),
    ("PHC-NL-01", "Pharmacist", 1, 0, "Open", "High", "No pharmacist recorded"),
    ("DH-MD-01", "Specialist Doctor", 4, 2, "Partially filled", "High", "Ophthalmology and medicine"),
    ("CHC-MD-01", "Lab Technician", 2, 1, "Partially filled", "Routine", "Lab support"),
    ("LAB-MD-01", "Lab Technician", 3, 3, "Filled", "Routine", ""),
]

# (application_code, alias, role, facility_code, qualification, experience, status)
APPLICATIONS = [
    ("APP-0001", "Applicant A01 (alias)", "Medical Officer", "CHC-BH-01", "MBBS (demo)", 4, "Shortlisted"),
    ("APP-0002", "Applicant A02 (alias)", "Staff Nurse", "CHC-NL-01", "GNM (demo)", 3, "Interview scheduled"),
    ("APP-0003", "Applicant A03 (alias)", "Lab Technician", "LAB-GOV-01", "DMLT (demo)", 5, "Offer"),
    ("APP-0004", "Applicant A04 (alias)", "Medical Officer", "PHC-AL-01", "MBBS (demo)", 2, "Received"),
    ("APP-0005", "Applicant A05 (alias)", "Pharmacist", "PHC-NL-01", "B.Pharm (demo)", 4, "Shortlisted"),
    ("APP-0006", "Applicant A06 (alias)", "Community Health Worker", "AAM-BR-01", "ASHA training (demo)", 2, "Received"),
    ("APP-0007", "Applicant A07 (alias)", "Specialist Doctor", "DH-MD-01", "MD (demo)", 8, "Interview scheduled"),
    ("APP-0008", "Applicant A08 (alias)", "Physiotherapist", "DH-01", "BPT (demo)", 3, "Rejected"),
    ("APP-0009", "Applicant A09 (alias)", "Staff Nurse", "DH-01", "GNM (demo)", 1, "Received"),
    ("APP-0010", "Applicant A10 (alias)", "Lab Technician", "CHC-MD-01", "DMLT (demo)", 6, "Offer"),
]

# (title, message, language, audience, target_area, channel, status)
CAMPAIGNS = [
    ("NCD screening awareness", "Attend the free NCD screening camp at your nearby health facility. Confirm timings with the facility.", "Telugu", "Adults 30+", "Bhuvanagiri", "Planned SMS", "Approved draft"),
    ("Maternal health follow-up", "Antenatal check-ups are available at listed facilities. Please confirm the schedule before visiting.", "Telugu", "Pregnant women and families", "Ramannapet", "Planned voice call", "Draft"),
    ("School vision screening", "Vision screening for children is planned at participating schools. Consent will be collected separately.", "Telugu", "Children aged 6-17 and parents", "Choutuppal", "Planned WhatsApp", "Needs review"),
    ("Substance-use awareness and counselling", "Confidential, voluntary counselling support is available through listed facilities. No punitive action is taken.", "Telugu", "Adolescents and adults", "Nalgonda", "Community session", "Approved draft"),
    ("Maternal nutrition awareness", "Nutrition counselling is available at Anganwadi and health facilities. Confirm timings with staff.", "Telugu", "Mothers and caregivers", "Medchal-Malkajgiri", "Planned voice call", "Draft"),
    ("Seasonal fever prevention", "Preventive advice is available at your local health facility. Seek emergency care for severe symptoms.", "Telugu", "General community", "Yadadri Bhuvanagiri", "Print / wall poster", "Needs review"),
]

# (title, message, audience, channel, status, related_entity, days_from_now)
NOTIFICATIONS = [
    ("Referral follow-up overdue", "Review open referrals with overdue follow-up dates and record the next action.", "Medical Officers", "Planned SMS", "Approved", "referral", 0),
    ("Laboratory result verification pending", "Results are awaiting clinician review. Verify within the demo workflow.", "Laboratory Administrators", "Planned SMS", "Approved", "lab_order", 1),
    ("Facility verification pending", "Facility records need verification before the directory is relied upon.", "Facility Administrators", "Notice board", "Draft", "facility", 2),
    ("Screening camp reminder", "Remember to confirm participant consent before screening intake.", "Community Health Workers", "Planned WhatsApp", "Simulated — sent", "screening_event", -1),
    ("Staffing gap escalation", "High-priority vacancies are impacting service availability in selected facilities.", "Facility Administrators", "Planned SMS", "Draft", "vacancy", 3),
    ("Citizen checkup reminder", "This is a simulated reminder. Real delivery requires consent, templates and provider integration.", "Citizens", "Planned SMS", "Simulated — sent", "screening", -2),
]

SUBSTANCE_CASES = [
    ("SU-0001", 0, "Tobacco", "Confidential screening recorded; counselling offered.", "Counselling scheduled", "Counsellor A (alias)", 3),
    ("SU-0002", 3, "Alcohol", "Confidential screening recorded; counselling offered.", "Counselling completed", "Counsellor B (alias)", -2),
    ("SU-0003", 15, "Tobacco & alcohol", "Counselling linkage recorded; no punitive action.", "Referred", "Counsellor A (alias)", 5),
    ("SU-0004", 20, "Tobacco", "Voluntary screening; follow-up planned.", "Screening recorded", "Unassigned", 7),
    ("SU-0005", 31, "Alcohol", "Counselling completed; follow-up scheduled.", "Counselling completed", "Counsellor B (alias)", 2),
    ("SU-0006", 34, "Tobacco", "Referred for confidential counselling.", "Referred", "Counsellor A (alias)", 4),
    ("SU-0007", 28, "Other", "Voluntary screening recorded; confidentiality maintained.", "Screening recorded", "Counsellor C (alias)", 6),
    ("SU-0008", 37, "Tobacco & alcohol", "Counselling completed and case closed.", "Closed", "Counsellor B (alias)", -5),
]

# (participant_index, facility_code, service, days_from_now, status)
APPOINTMENTS = [
    (0, "CHC-BH-01", "NCD screening", 2, "Confirmed"),
    (3, "CHC-CH-01", "General medicine", 1, "Requested"),
    (4, "PHC-RM-01", "Maternal health", 3, "Confirmed"),
    (9, "AAM-BH-01", "Wellness counselling", -2, "Attended"),
    (31, "CHC-NL-01", "NCD screening", 4, "Requested"),
    (34, "PHC-MD-01", "General medicine", 2, "Confirmed"),
    (37, "AAM-MD-01", "Vision screening", -3, "Missed"),
    (20, "CHC-BH-01", "Substance-use counselling", 5, "Requested"),
]


def seed_database(session: Session) -> dict[str, int]:
    """Insert the deterministic demo dataset if the database is empty."""
    if session.scalar(select(Facility).limit(1)) is not None:
        return _counts(session)

    facilities: list[Facility] = []
    fac_by_code: dict[str, Facility] = {}
    for (code, name, ftype, district, mandal, locality, lat, lon, addr,
         verif, op, active, ownership, beds, catchment, cap) in FACILITIES:
        f = Facility(
            code=code, name=name, type=ftype, state="Telangana (illustrative)",
            district=district, mandal=mandal, locality=locality, latitude=lat,
            longitude=lon, address_label=addr, verification_status=verif,
            operating_status=op, is_active=active, ownership=ownership,
            beds=beds, catchment_population=catchment, capacity_notes=cap,
        )
        facilities.append(f)
        fac_by_code[code] = f
    session.add_all(facilities)
    session.flush()

    for code, services in SERVICE_MAP.items():
        for service_name, category, capacity, note in services:
            session.add(Service(
                facility_id=fac_by_code[code].id, service_name=service_name,
                category=category, availability_note=note,
                capacity_per_period=capacity, active=True,
            ))

    participants: list[Participant] = []
    for idx, (code, alias, band, gender, locality, district) in enumerate(PARTICIPANTS):
        p = Participant(
            synthetic_code=code, display_name_alias=alias, age_band=band,
            gender=gender, locality=locality, district=district,
            consent_status="Granted (demo)", assigned_worker=WORKERS[idx % len(WORKERS)],
        )
        participants.append(p)
        session.add(p)

    programmes: list[Programme] = []
    for name, desc, cohort, eligibility, ref, start, end, status in PROGRAMMES:
        prog = Programme(
            name=name, description=desc, cohort_text=cohort, eligibility_notes=eligibility,
            guidance_reference=ref, start_date=start, end_date=end, status=status,
        )
        programmes.append(prog)
        session.add(prog)

    for code, name, role, qual, fac_code, skills, avail, shift, emp in STAFF:
        session.add(Staff(
            staff_code=code, display_name=name, role=role, qualification=qual,
            facility_id=fac_by_code[fac_code].id, skills=skills,
            availability=avail, shift=shift, employment_type=emp,
            verification_status="Verified" if code not in {"S-011", "S-021"} else "Pending verification",
        ))

    session.flush()

    events: list[ScreeningEvent] = []
    for code, prog_idx, fac_code, name, days_ago, status, attendance in EVENTS:
        ev = ScreeningEvent(
            event_code=code, programme_id=programmes[prog_idx].id,
            facility_id=fac_by_code[fac_code].id, event_name=name,
            event_date=_d(days_ago), status=status, attendance_count=attendance,
        )
        events.append(ev)
        session.add(ev)
    session.flush()

    screenings: list[Screening] = []
    for event_idx, part_idx, stype, obs, cat, review in SCREENINGS:
        s = Screening(
            participant_id=participants[part_idx].id, event_id=events[event_idx].id,
            screening_type=stype, observation_text=obs, result_category=cat,
            review_status=review,
            reviewed_by="Dr. Rao (alias)" if review == "Reviewed" else None,
            created_at=datetime.combine(events[event_idx].event_date, datetime.min.time(), tzinfo=timezone.utc),
        )
        screenings.append(s)
        session.add(s)
    session.flush()

    referrals: list[Referral] = []
    for i, (scr_idx, src, dst, reason, priority, status, days_ago, note) in enumerate(REFERRALS):
        scr = screenings[scr_idx]
        referral = Referral(
            referral_code=f"REF-{i + 1:04d}", participant_id=scr.participant_id,
            screening_id=scr.id, source_facility_id=fac_by_code[src].id,
            destination_facility_id=fac_by_code[dst].id, reason_category=reason,
            priority=priority, status=status, referring_doctor="Dr. Rao (alias)",
            created_by="Dr. Rao (alias)",
            created_at=datetime.now(timezone.utc) - timedelta(days=days_ago + 1),
            follow_up_date=_d(days_ago),
            closed_at=datetime.now(timezone.utc) - timedelta(days=1) if status == "Completed" else None,
            closure_note=note,
        )
        referrals.append(referral)
        session.add(referral)
    session.flush()

    for i, (ref_idx, lab_code, test, priority, result_status, reviewer, report_status) in enumerate(LAB_SPECS):
        ref = referrals[ref_idx]
        sample_status = {
            "Ordered": "Ordered", "Sample collected": "Sample collected",
            "Received by lab": "Received by lab", "Processing": "Processing",
            "Result available": "Processing",
        }.get(result_status, "Processing")
        session.add(LabOrder(
            order_code=f"LAB-{i + 1:04d}", referral_id=ref.id,
            lab_facility_id=fac_by_code[lab_code].id, test_category=test,
            priority=priority, requested_by="Dr. Rao (alias)",
            sample_status=sample_status, result_status=result_status,
            report_status=report_status, reviewer_status=reviewer,
        ))

    for i, (fac_code, role, required, filled, status, priority, notes) in enumerate(VACANCIES):
        session.add(StaffVacancy(
            vacancy_code=f"VAC-{i + 1:04d}", facility_id=fac_by_code[fac_code].id,
            role=role, required_count=required, filled_count=filled,
            status=status, priority=priority, notes=notes,
        ))

    for code, alias, role, fac_code, qual, exp, status in APPLICATIONS:
        session.add(EmploymentApplication(
            application_code=code, applicant_alias=alias, role=role,
            facility_id=fac_by_code[fac_code].id, qualification=qual,
            experience_years=exp, status=status,
        ))

    for i, (title, msg, lang, audience, area, channel, status) in enumerate(CAMPAIGNS):
        session.add(Campaign(
            title=title, message=msg, language=lang, audience=audience,
            target_area=area, planned_channel=channel,
            schedule_at=_dt(i + 2), status=status,
            responsible_facility_id=fac_by_code["CHC-BH-01"].id,
            delivery_status="Simulated — not sent", created_by="Demo administrator",
        ))

    for i, (title, msg, audience, channel, status, related, offset) in enumerate(NOTIFICATIONS):
        session.add(Notification(
            title=title, message=msg, audience=audience, channel=channel,
            status=status, related_entity=related, schedule_at=_dt(offset),
            created_by="Demo administrator",
        ))

    for code, part_idx, substance, note, status, counsellor, offset in SUBSTANCE_CASES:
        session.add(SubstanceUseCase(
            case_code=code, participant_id=participants[part_idx].id,
            substance_category=substance, screening_note=note,
            consent_status="Granted (demo)",
            confidentiality_level="Restricted — counselling team only",
            counselling_status=status, assigned_counsellor=counsellor,
            follow_up_date=_dt(offset),
        ))

    for i, (part_idx, fac_code, service, offset, status) in enumerate(APPOINTMENTS):
        session.add(Appointment(
            appointment_code=f"APT-{i + 1:04d}", participant_id=participants[part_idx].id,
            facility_id=fac_by_code[fac_code].id, service_name=service,
            preferred_date=_dt(offset), status=status,
        ))

    session.add_all([
        AuditEvent(actor_role="District Administrator", action="Seeded demo dataset",
                   entity_type="database", entity_id="seed", note="Deterministic synthetic data"),
        AuditEvent(actor_role="Medical Officer", action="Reviewed screening observations",
                   entity_type="screening", entity_id="batch", note="Demo review"),
    ])
    session.flush()
    return _counts(session)


def _counts(session: Session) -> dict[str, int]:
    def count(model):
        return int(session.scalar(select(func.count()).select_from(model)) or 0)

    return {
        "facilities": count(Facility),
        "services": count(Service),
        "participants": count(Participant),
        "programmes": count(Programme),
        "screening_events": count(ScreeningEvent),
        "screenings": count(Screening),
        "referrals": count(Referral),
        "lab_orders": count(LabOrder),
        "campaigns": count(Campaign),
        "staff": count(Staff),
        "vacancies": count(StaffVacancy),
        "applications": count(EmploymentApplication),
        "notifications": count(Notification),
        "substance_cases": count(SubstanceUseCase),
        "appointments": count(Appointment),
    }


def reset_database(session: Session) -> dict[str, int]:
    """Drop all demo rows and re-seed deterministically."""
    from src.models import Base

    for table in reversed(Base.metadata.sorted_tables):
        session.execute(delete(table))
    session.flush()
    return seed_database(session)
