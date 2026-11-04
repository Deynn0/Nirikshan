"""Insight Engine: Proof generation for approval checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel, Field
from starlette.testclient import TestClient

from nirikshan.advisory.extractor import (
    FieldExtractor,
    OllamaConnectionError,
    OllamaFieldExtractor,
    StubFieldExtractor,
)
from nirikshan.advisory.grounding import (
    GroundedVerifier,
    RecognizedDocument,
)
from nirikshan.main import app
from nirikshan.trust.ladder import TrustLevel


class SampleRegulatorySchema(BaseModel):
    land_area_acres: float = Field(..., description="Total land area in acres")
    survey_no: str = Field(..., description="Land survey number")
    fire_noc_expiry_date: str = Field(..., description="Fire NOC expiry date (YYYY-MM-DD)")


TEST_DOC_TEXT = (
    "AICTE Approval Process Handbook — Scrutiny Document\n"
    "Institution: Aryabhata College of Engineering.\n"
    "Location: Urban area.\n"
    "Land Title: The institution possesses 5.2 acres under Survey No: 123/4A.\n"
    "Fire NOC: State Fire Service NOC valid until 2025-12-31.\n"
)


# ---------------------------------------------------------------------------
# Field Extractor Abstraction & Prompt Building
# ---------------------------------------------------------------------------

def test_field_extractor_schema_prompt_formatting() -> None:
    extractor = StubFieldExtractor()
    prompt = extractor.build_schema_prompt(SampleRegulatorySchema)
    assert "land_area_acres" in prompt
    assert "survey_no" in prompt
    assert "fire_noc_expiry_date" in prompt
    assert "CRITICAL RULES:" in prompt
    assert "Do NOT hallucinate values" in prompt


def test_stub_field_extractor_heuristic_extraction() -> None:
    extractor = StubFieldExtractor()
    extracted = extractor.extract(TEST_DOC_TEXT, schema=SampleRegulatorySchema)
    assert extracted["land_area_acres"] == 5.2
    assert extracted["survey_no"] == "123/4A"
    assert extracted["fire_noc_expiry_date"] == "2025-12-31"


def test_stub_field_extractor_fixed_output() -> None:
    mock_dict = {"custom_field": "approved", "score": 98}
    extractor = StubFieldExtractor(fixed_output=mock_dict)
    assert extractor.extract("any text") == mock_dict


def test_extractor_clean_json_response() -> None:
    wrapped = "```json\n{\"land_area_acres\": 7.5, \"survey_no\": \"88/1\"}\n```"
    parsed = FieldExtractor.clean_json_response(wrapped)
    assert parsed["land_area_acres"] == 7.5
    assert parsed["survey_no"] == "88/1"

    messy = "Here is the extracted JSON output:\n{\"valid\": true}\nHope this helps!"
    parsed_messy = FieldExtractor.clean_json_response(messy)
    assert parsed_messy["valid"] is True


def test_ollama_extractor_connection_error() -> None:
    extractor = OllamaFieldExtractor(base_url="http://127.0.0.1:59999", timeout=0.5)
    with pytest.raises(OllamaConnectionError):
        extractor.extract("test text", schema={"test": "string"})


# ---------------------------------------------------------------------------
# Grounded Verification & Proof Generation
# ---------------------------------------------------------------------------

def test_grounding_exact_match_success() -> None:
    verifier = GroundedVerifier()
    doc = RecognizedDocument.from_text_pages([TEST_DOC_TEXT])
    extracted = {"land_area_acres": 5.2, "survey_no": "123/4A"}
    result = verifier.verify_and_ground(extracted, doc)

    assert result.is_fully_grounded
    assert len(result.grounded_fields) == 2
    assert "land_area_acres" in result.grounded_fields
    assert "survey_no" in result.grounded_fields

    field_land = result.grounded_fields["land_area_acres"]
    assert field_land.value == 5.2
    assert field_land.confidence == 1.0
    assert field_land.match_type == "exact"
    assert field_land.page == 1

    ev = field_land.to_evidence_item("doc-01", "deed.pdf")
    assert ev.trust_level == TrustLevel.MODEL
    assert ev.is_decisive is False


def test_grounding_normalized_fuzzy_match() -> None:
    verifier = GroundedVerifier(fuzzy_threshold=0.80)
    doc = RecognizedDocument.from_text_pages([TEST_DOC_TEXT])
    extracted = {"survey_no": "123-4A"}

    result = verifier.verify_and_ground(extracted, doc)
    assert "survey_no" in result.grounded_fields
    grounded = result.grounded_fields["survey_no"]
    assert grounded.confidence >= 0.80


def test_grounding_rejects_fabricated_value() -> None:
    """Proof generation strictly rejects fabricated/hallucinated values."""
    verifier = GroundedVerifier()
    doc = RecognizedDocument.from_text_pages([TEST_DOC_TEXT])

    extracted = {
        "land_area_acres": 5.2,
        "fabricated_land_area": 99.85,
        "hallucinated_survey": "NON-EXISTENT/999/XYZ",
    }
    result = verifier.verify_and_ground(extracted, doc)

    assert "land_area_acres" in result.grounded_fields
    assert "fabricated_land_area" not in result.grounded_fields
    assert "hallucinated_survey" not in result.grounded_fields

    assert "fabricated_land_area" in result.rejected_fields
    assert result.rejection_reasons["fabricated_land_area"] == "hallucination_rejected"
    assert any("hallucination_rejected: field 'fabricated_land_area'" in log for log in result.hallucination_log)
    assert not result.is_fully_grounded


# ---------------------------------------------------------------------------
# API Advisory Extract and Ground Proof
# ---------------------------------------------------------------------------

def test_api_advisory_extract_and_ground() -> None:
    client = TestClient(app)
    payload = {
        "text": TEST_DOC_TEXT,
        "schema_definition": {"land_area_acres": "number", "survey_no": "string"},
    }
    response = client.post("/api/advisory/extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "grounded_fields" in data
    assert "land_area_acres" in data["grounded_fields"]
    assert data["grounded_fields"]["land_area_acres"]["value"] == 5.2
    assert data["grounded_fields"]["land_area_acres"]["confidence"] == 1.0

