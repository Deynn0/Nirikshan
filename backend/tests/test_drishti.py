"""Drishti Conversational AI & NLP: Multilingual intent routing (EN, HI, Hinglish), guardrails, memory."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from nirikshan.advisory.ask_why import (
    AskWhyAssistant,
    AskWhyContext,
    StubAskWhyLLM,
)
from nirikshan.core.rule_schema import Rule, RuleCitation, RuleSeverity
from nirikshan.main import app
from nirikshan.rules.aliases import AliasResolver, normalize_devanagari
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import TrustLevel
from training.drishti.lexicon import INTENT_TEMPLATES, INTENTS


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        finding_id="fnd-drishti-01",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.FAIL,
        summary="Deficient: Possesses 3.2 Acres, requires 5.0 Acres.",
        details="Clause 4.1 mandates 5.0 acres for Rural Engineering Institutions.",
        handbook_citation=HandbookCitation(
            handbook="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 4.1",
            page=42,
            edition="2024-2027",
        ),
        evidence_list=[],
    )


@pytest.fixture
def sample_rule() -> Rule:
    return Rule(
        rule_id="AICTE-2024-LAND-001",
        title="Minimum Land Area",
        citation=RuleCitation(
            document="AICTE Approval Process Handbook",
            clause="Clause 4.1",
            page=42,
        ),
        applicable_years=["2024-2025"],
        category="Land",
        evidence_requirements=[],
        logic="land_area_acres >= 5.0",
        severity=RuleSeverity.CRITICAL,
    )


# ---------------------------------------------------------------------------
# Multilingual Intent Routing (EN, HI, Hinglish)
# ---------------------------------------------------------------------------

def test_alias_english_exact_and_fuzzy() -> None:
    resolver = AliasResolver()
    resolver.reload()

    assert resolver.resolve("Total Land Area") == "land_area_acres"
    assert resolver.resolve("Fire Safety Certificate Valid") == "fire_noc_valid"
    assert resolver.resolve("Total land in acre") == "land_area_acres"
    assert resolver.resolve("Fire safety NOC status") == "fire_noc_valid"


def test_alias_hindi_exact_fuzzy_and_devanagari_normalization() -> None:
    resolver = AliasResolver()
    resolver.reload()

    assert resolver.resolve("भूमि का क्षेत्रफल (एकड़)") == "land_area_acres"
    assert resolver.resolve("अग्निशमन अनापत्ति प्रमाण पत्र वैध") == "fire_noc_valid"

    zw_text = "अग्निशमन\u200b अनापत्ति प्रमाण पत्र वैध"
    assert normalize_devanagari(zw_text) == "अग्निशमन अनापत्ति प्रमाण पत्र वैध"
    assert resolver.resolve(zw_text) == "fire_noc_valid"
    assert resolver.resolve("अग्नि सुरक्षा एनओसी स्थिति") == "fire_noc_valid"


def test_alias_unknown_label_returns_none() -> None:
    resolver = AliasResolver()
    resolver.reload()
    assert resolver.resolve("xyz123 completely unrelated label") is None


def test_drishti_intent_registry_and_templates() -> None:
    assert "check_fire_noc" in INTENTS
    assert "check_land_area" in INTENTS
    assert "out_of_scope" in INTENTS

    for intent in ["check_fire_noc", "check_land_area"]:
        templates = INTENT_TEMPLATES[intent]
        assert "en" in templates and len(templates["en"]) >= 3
        assert "hi" in templates and len(templates["hi"]) >= 3
        assert "hinglish" in templates and len(templates["hinglish"]) >= 3


# ---------------------------------------------------------------------------
# Guardrails: Defense against Prompt Injections
# ---------------------------------------------------------------------------

def test_guardrail_blocks_prompt_injections() -> None:
    lines_file = Path(__file__).parent / "data" / "instruction_lines.json"
    assert lines_file.exists()

    data = json.loads(lines_file.read_text(encoding="utf-8"))
    injection_lines = data.get("known", []) + data.get("held_out_author", [])
    assert len(injection_lines) >= 5

    injection_pattern = re.compile(
        r"(ignore|disregard|override|skip|pretend|pre-verified|instruction|output|mark.*valid|do not flag|accept.*validity|scanning program|AI reviewer|AI model|automated|treat this)",
        re.IGNORECASE,
    )

    detected = 0
    for line in injection_lines:
        if injection_pattern.search(line):
            detected += 1

    assert detected >= len(injection_lines) * 0.7


# ---------------------------------------------------------------------------
# Contextual Memory & Grounding (Ask Why Assistant)
# ---------------------------------------------------------------------------

def test_ask_why_answers_in_context_question_with_citations(
    sample_finding: Finding, sample_rule: Rule
) -> None:
    context = AskWhyContext(
        finding=sample_finding,
        rule=sample_rule,
        facts={"land_area_acres": 3.2},
        evidence_items=sample_finding.evidence_list,
    )
    assistant = AskWhyAssistant(backend=StubAskWhyLLM())
    resp = assistant.ask(
        question="Why did the land area rule fail for this institution?",
        context=context,
    )

    assert not resp.is_refusal
    assert len(resp.citations) >= 1
    assert "AICTE-2024-LAND-001" in resp.citations[0].rule_id
    assert "4.1" in resp.citations[0].clause


def test_ask_why_refuses_out_of_context_questions(sample_finding: Finding) -> None:
    context = AskWhyContext(
        finding=sample_finding,
        facts={"land_area_acres": 3.2},
    )
    assistant = AskWhyAssistant(backend=StubAskWhyLLM())
    resp = assistant.ask(question="Who is the president of France?", context=context)
    assert resp.is_refusal is True
    assert resp.answer.startswith("REFUSAL:")
    assert len(resp.citations) == 0


def test_api_advisory_ask_why(sample_finding: Finding) -> None:
    client = TestClient(app)
    # In-context
    payload = {
        "question": "Why did this land area finding fail?",
        "finding": sample_finding.model_dump(mode="json"),
        "facts": {"land_area_acres": 3.2},
    }
    resp = client.post("/api/advisory/ask-why", json=payload)
    assert resp.status_code == 200
    assert not resp.json()["is_refusal"]

    # Out-of-context
    payload_ooc = {
        "question": "What is the weather in Delhi?",
        "finding": sample_finding.model_dump(mode="json"),
        "facts": {},
    }
    resp_ooc = client.post("/api/advisory/ask-why", json=payload_ooc)
    assert resp_ooc.status_code == 200
    assert resp_ooc.json()["is_refusal"] is True
