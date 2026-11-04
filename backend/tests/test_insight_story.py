"""Insight Engine: Chronological application narrative generation."""

from __future__ import annotations

import datetime
from datetime import UTC, datetime, timedelta

import pytest

from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import TrustLevel


def _generate_application_story(
    dossier: ApplicationDossier,
    events: list[dict],
) -> dict:
    """Build a chronological narrative story of an application's scrutiny journey."""
    sorted_events = sorted(events, key=lambda e: e["timestamp"])

    narrative_paragraphs = []
    narrative_paragraphs.append(
        f"Application {dossier.application_number} was submitted by {dossier.institution_name} "
        f"for {dossier.program} ({dossier.level}) in {dossier.location_type} zone."
    )

    for event in sorted_events:
        stage = event.get("stage")
        actor = event.get("actor")
        ts_str = event.get("timestamp")
        summary = event.get("summary")
        narrative_paragraphs.append(f"[{ts_str}] {actor} ({stage}): {summary}")

    return {
        "dossier_id": dossier.dossier_id,
        "application_number": dossier.application_number,
        "chronological_events": sorted_events,
        "narrative_text": "\n".join(narrative_paragraphs),
        "total_milestones": len(sorted_events),
    }


def test_chronological_application_story_generation() -> None:
    """Validate timeline reconstruction and chronological narrative story generation."""
    t0 = datetime.now(UTC)
    dossier = ApplicationDossier(
        dossier_id="dos-story-01",
        institution_name="Vikram Sarabhai Institute of Space Technology",
        application_number="AICTE/2024/VSIST/001",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Government",
        location_type="Urban",
        intake_proposed=360,
    )

    # Milestones intentionally out of order to verify sorting
    milestones = [
        {
            "stage": "HANDOFF",
            "actor": "Executive Committee",
            "timestamp": (t0 + timedelta(days=5)).isoformat(),
            "summary": "Scrutiny report received with cryptographic seal; approval recommended.",
        },
        {
            "stage": "SUBMISSION",
            "actor": "Applicant",
            "timestamp": t0.isoformat(),
            "summary": "Application dossier submitted with 4 institutional documents.",
        },
        {
            "stage": "FORENSIC_SCAN",
            "actor": "Forensics Engine",
            "timestamp": (t0 + timedelta(hours=2)).isoformat(),
            "summary": "Forensic scan completed: zero whiteout or incremental update anomalies detected.",
        },
        {
            "stage": "EVALUATION",
            "actor": "Rule Engine",
            "timestamp": (t0 + timedelta(hours=3)).isoformat(),
            "summary": "Rule evaluation completed against APH 2024-2027: 10 statutory rules satisfied.",
        },
        {
            "stage": "OFFICER_REVIEW",
            "actor": "Scrutiny Officer",
            "timestamp": (t0 + timedelta(days=2)).isoformat(),
            "summary": "Desk officer verified institutional land deeds and signed scrutiny clearance.",
        },
    ]

    story = _generate_application_story(dossier, milestones)

    assert story["dossier_id"] == "dos-story-01"
    assert story["total_milestones"] == 5
    # Verify strict ascending order of milestones
    chronological = story["chronological_events"]
    assert chronological[0]["stage"] == "SUBMISSION"
    assert chronological[1]["stage"] == "FORENSIC_SCAN"
    assert chronological[2]["stage"] == "EVALUATION"
    assert chronological[3]["stage"] == "OFFICER_REVIEW"
    assert chronological[4]["stage"] == "HANDOFF"

    # Verify narrative text formatting
    narrative = story["narrative_text"]
    assert "Vikram Sarabhai Institute of Space Technology" in narrative
    assert "Applicant (SUBMISSION):" in narrative
    assert "Executive Committee (HANDOFF):" in narrative


def test_story_narrative_with_rectification_loop() -> None:
    """Validate narrative generation when a rectification request occurs mid-stream."""
    t0 = datetime.now(UTC)
    dossier = ApplicationDossier(
        dossier_id="dos-story-02",
        institution_name="Aryabhata College",
        application_number="AICTE/2024/ARYA/001",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
    )
    milestones = [
        {
            "stage": "SUBMISSION",
            "actor": "Applicant",
            "timestamp": t0.isoformat(),
            "summary": "Initial submission.",
        },
        {
            "stage": "RECTIFICATION_REQUEST",
            "actor": "Scrutiny Officer",
            "timestamp": (t0 + timedelta(days=1)).isoformat(),
            "summary": "Discrepancy noted in Fire Safety NOC expiry date; rectification requested.",
        },
        {
            "stage": "RECTIFICATION_UPLOAD",
            "actor": "Applicant",
            "timestamp": (t0 + timedelta(days=2)).isoformat(),
            "summary": "Uploaded renewed State Fire Department endorsement.",
        },
        {
            "stage": "CLEARANCE",
            "actor": "Scrutiny Officer",
            "timestamp": (t0 + timedelta(days=3)).isoformat(),
            "summary": "Rectified document verified and cleared.",
        },
    ]
    story = _generate_application_story(dossier, milestones)
    assert len(story["chronological_events"]) == 4
    assert story["chronological_events"][1]["stage"] == "RECTIFICATION_REQUEST"
    assert story["chronological_events"][2]["stage"] == "RECTIFICATION_UPLOAD"
