"""Optional AI assistance with deterministic, offline-safe fallbacks.

The assistant only performs administrative and explanatory tasks. It never
diagnoses, prescribes or decides care. When no provider is configured the
deterministic fallbacks below still produce grounded, useful text.
"""
from __future__ import annotations

import os
from typing import Callable

from sqlalchemy.orm import Session

from src.config import AI_ENABLED, AI_MODEL, SIMULATED_BANNER
from src.services import facility_service, reporting_service

DISCLAIMER = "Draft administrative assistance — a human must review before use. Not medical advice."


def is_enabled() -> bool:
    return AI_ENABLED


def status_text() -> str:
    if AI_ENABLED:
        return f"AI assistant enabled ({AI_MODEL}). Outputs are drafts only and require human review."
    return (
        "AI assistant disabled (no provider configured). Deterministic, database-grounded fallbacks are shown. "
        "Core workflows remain fully usable."
    )


def _call_llm(prompt: str) -> str | None:
    """Optional provider hook. Disabled unless explicitly configured.

    Kept intentionally minimal: no real patient data is ever sent, and the app
    works without this function. Add an approved provider adapter here.
    """
    if not AI_ENABLED:
        return None
    api_key = os.getenv("BHDC_AI_API_KEY")
    if not api_key:
        return None
    return None  # Provider integration intentionally out of scope for the demo.


def facility_navigation(session: Session, service: str, mandal: str) -> str:
    matches = facility_service.search_facilities(session, mandal=mandal, service=service)
    if not matches:
        return (
            f"No listed facility currently offers '{service}' in {mandal}. Try a nearby mandal or the district "
            f"hospital, and call ahead to confirm availability.\n\n{DISCLAIMER}"
        )
    lines = [f"Listed options for '{service}' in {mandal}:"]
    for facility in matches[:6]:
        lines.append(
            f"• {facility.name} ({facility.type}) — {facility.locality}; "
            f"status: {facility.operating_status}; verification: {facility.verification_status}."
        )
    lines.append("Availability must be confirmed directly with the facility. This is directory guidance, not a booking.")
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def admin_summary(session: Session) -> str:
    kpis = reporting_service.dashboard_kpis(session)
    text = (
        f"District operations snapshot ({kpis['facilities']} listed facilities, "
        f"{kpis['services']} listed services).\n"
        f"• Screening events: {kpis['screening_events']} covering {kpis['screenings']} observations.\n"
        f"• Referrals open: {kpis['referrals_open']}; follow-ups overdue: {kpis['followups_overdue']}.\n"
        f"• Screening observations awaiting clinician review: {kpis['pending_reviews']}.\n"
        f"• Laboratory results awaiting clinician review: {kpis['lab_awaiting_review']}.\n"
        f"• Facilities pending verification: {kpis['pending_verification']}.\n\n"
        f"Aggregated, non-identifiable demo data. {DISCLAIMER}"
    )
    generated = _call_llm(text)
    return generated or text


def campaign_draft(topic: str, audience: str, language: str) -> str:
    topic = topic.strip() or "health screening"
    audience = audience.strip() or "community members"
    draft = (
        f"Draft awareness message ({language})\n"
        f"Audience: {audience}\n"
        f"Topic: {topic}\n\n"
        f"Message: A {topic} service is available through listed health facilities in your area. "
        f"Please contact or visit the nearest listed facility to confirm timings and eligibility. "
        f"If you have severe or urgent symptoms, seek emergency care immediately and do not wait.\n\n"
        f"{DISCLAIMER}"
    )
    generated = _call_llm(draft)
    return generated or draft


def faq_answer(session: Session, question: str) -> str:
    q = question.lower()
    if any(word in q for word in ["emergency", "chest pain", "bleeding", "breathless"]):
        return (
            "If there is severe or immediate danger, contact local emergency services or go to the nearest "
            "emergency department now. Do not wait for app navigation. This prototype does not provide emergency care."
        )
    if "screening" in q or "diagnos" in q:
        return (
            "A screening observation is not a diagnosis. Flagged screenings require clinician review and "
            "confirmation before any clinical conclusion. This prototype does not diagnose or prescribe."
        )
    if "data" in q or "privacy" in q:
        return (
            "This prototype uses fictional demonstration data only. No real patient records, Aadhaar/ABHA IDs "
            "or phone numbers are stored or transmitted."
        )
    if "referral" in q:
        return (
            "Referrals move through Draft → Sent → Accepted → Scheduled → Attended → Completed. "
            "Overdue follow-ups are highlighted, and urgent cases must go to an emergency-capable facility."
        )
    kpis = reporting_service.dashboard_kpis(session)
    return (
        f"I don't have a specific answer for that. The demo currently lists {kpis['facilities']} facilities and "
        f"{kpis['services']} services. Try the Facility Directory or the About & Safety tab.\n\n{SIMULATED_BANNER}"
    )
