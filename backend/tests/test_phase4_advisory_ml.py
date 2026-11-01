"""Tests for Phase 4: Advisory ML Layer.

Tests all five deliverables:
1. FieldExtractor abstraction with Ollama and Stub backends
2. Grounded verification: exact & fuzzy matching, rejecting fabricated values (hallucination_rejected)
3. Fine-tuning scaffold: dataset builder, train safety guard, evaluate metrics
4. Lab asset counter: mock detector, image annotation, inventory comparison, advisory Finding
5. Ask Why assistant: grounded answering with citations and strict refusal of out-of-context questions
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import BaseModel, Field

from nirikshan.advisory.ask_why import (
    AskWhyAssistant,
    AskWhyContext,
    StubAskWhyLLM,
)
from nirikshan.advisory.asset_counter import (
    DetectionBox,
    MockLabAssetDetector,
    YOLOXAssetDetector,
    annotate_image,
    verify_lab_inventory,
)
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
from nirikshan.core.rule_schema import Rule, RuleCitation, RuleSeverity
from nirikshan.main import app
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import EvidenceItem, TrustLevel
from training.dataset_builder import generate_synthetic_record
from training.evaluate import evaluate_predictions

# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

TEST_DOC_TEXT = (
    "AICTE Approval Process Handbook — Scrutiny Document\n"
    "Institution: Aryabhata College of Engineering.\n"
    "Location: Urban area.\n"
    "Land Title: The institution possesses 5.2 acres under Survey No: 123/4A.\n"
    "Fire NOC: State Fire Service NOC valid until 2025-12-31.\n"
    "Laboratory Audit: 60 computer workstations installed in Room 204.\n"
)


class SampleRegulatorySchema(BaseModel):
    land_area_acres: float = Field(..., description="Campus land area in acres")
    survey_no: str = Field(..., description="Survey or Khasra parcel number")
    fire_noc_expiry_date: str = Field(..., description="Fire NOC validity date YYYY-MM-DD")


@pytest.fixture
def test_image(tmp_path: Path) -> Path:
    """Create a temporary synthetic lab photograph."""
    img_path = tmp_path / "test_lab_photo.jpg"
    img = Image.new("RGB", (640, 480), color=(60, 70, 90))
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_finding() -> Finding:
    """Sample verification finding for Ask Why testing."""
    return Finding(
        finding_id="fnd-land-test-01",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Area Requirement",
        category="Land",
        status=VerificationStatus.FAIL,
        summary="Required 5.0 acres in Urban zone; only 3.2 acres verified.",
        details="Clause 4.1 mandates 5.0 contiguous acres for mega/urban engineering campuses.",
        handbook_citation=HandbookCitation(
            handbook="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 4.1",
            page=32,
            table="Table 4.1",
        ),
        evidence_list=[
            EvidenceItem(
                evidence_id="ev-land-01",
                trust_level=TrustLevel.RECORD,
                source_type="LAND_SALE_DEED",
                description="Sub-Registrar Registered Sale Deed records 3.2 acres",
                source_document_id="doc-land-001",
                source_document_name="registered_deed.pdf",
                verification_method="SUB_REGISTRAR_SEAL",
            )
        ],
    )


# ===========================================================================
# 1. DELIVERABLE 1: Extractor Service
# ===========================================================================


def test_field_extractor_schema_prompt_formatting() -> None:
    """Extractor formats schema prompt instructions conforming to Pydantic and dict schemas."""
    extractor = StubFieldExtractor()
    prompt = extractor.build_schema_prompt(SampleRegulatorySchema)

    assert "land_area_acres" in prompt
    assert "survey_no" in prompt
    assert "fire_noc_expiry_date" in prompt
    assert "CRITICAL RULES:" in prompt
    assert "Do NOT hallucinate values" in prompt


def test_stub_field_extractor_heuristic_extraction() -> None:
    """Stub extractor correctly extracts structured values from document text using heuristics."""
    extractor = StubFieldExtractor()
    extracted = extractor.extract(TEST_DOC_TEXT, schema=SampleRegulatorySchema)

    assert extracted["land_area_acres"] == 5.2
    assert extracted["survey_no"] == "123/4A"
    assert extracted["fire_noc_expiry_date"] == "2025-12-31"


def test_stub_field_extractor_fixed_output() -> None:
    """Stub extractor returns injected fixed output when configured."""
    mock_dict = {"custom_field": "approved", "score": 98}
    extractor = StubFieldExtractor(fixed_output=mock_dict)
    res = extractor.extract("any text")
    assert res == mock_dict


def test_extractor_clean_json_response() -> None:
    """FieldExtractor.clean_json_response parses JSON with markdown blocks and leading text."""
    wrapped = "```json\n{\"land_area_acres\": 7.5, \"survey_no\": \"88/1\"}\n```"
    parsed = FieldExtractor.clean_json_response(wrapped)
    assert parsed["land_area_acres"] == 7.5
    assert parsed["survey_no"] == "88/1"

    messy = "Here is the extracted JSON output:\n{\"valid\": true}\nHope this helps!"
    parsed_messy = FieldExtractor.clean_json_response(messy)
    assert parsed_messy["valid"] is True


def test_ollama_extractor_connection_error() -> None:
    """OllamaFieldExtractor raises OllamaConnectionError when server is unavailable."""
    extractor = OllamaFieldExtractor(base_url="http://127.0.0.1:59999", timeout=0.5)
    with pytest.raises(OllamaConnectionError):
        extractor.extract("test text", schema={"test": "string"})


# ===========================================================================
# 2. DELIVERABLE 2: Grounded Verification
# ===========================================================================


def test_grounding_exact_match_success() -> None:
    """Grounded verification locates exact field values with bounding boxes and 1.0 confidence."""
    verifier = GroundedVerifier()
    doc = RecognizedDocument.from_text_pages([TEST_DOC_TEXT])

    extracted = {
        "land_area_acres": 5.2,
        "survey_no": "123/4A",
    }
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
    assert field_land.bbox.x >= 0
    assert field_land.bbox.width > 0

    # Evidence item conversion adheres to Trust Level MODEL
    ev = field_land.to_evidence_item("doc-01", "deed.pdf")
    assert ev.trust_level == TrustLevel.MODEL
    assert ev.is_decisive is False
    assert ev.verification_method == "GROUNDED_LLM_EXTRACTION"


def test_grounding_normalized_fuzzy_match() -> None:
    """Grounded verification matches normalized values with punctuation variations."""
    verifier = GroundedVerifier(fuzzy_threshold=0.80)
    # Document has "123/4A", model extracted "123-4A"
    doc = RecognizedDocument.from_text_pages([TEST_DOC_TEXT])
    extracted = {"survey_no": "123-4A"}

    result = verifier.verify_and_ground(extracted, doc)
    assert "survey_no" in result.grounded_fields
    grounded = result.grounded_fields["survey_no"]
    assert grounded.confidence >= 0.80
    assert grounded.bbox.width > 0


def test_grounding_rejects_fabricated_value() -> None:
    """MANDATORY TEST: Grounding rejects fabricated/hallucinated values, logs hallucination_rejected, and discards."""
    verifier = GroundedVerifier()
    doc = RecognizedDocument.from_text_pages([TEST_DOC_TEXT])

    extracted = {
        "land_area_acres": 5.2,  # Present in document
        "fabricated_land_area": 99.85,  # Hallucinated! NOT in document
        "hallucinated_survey": "NON-EXISTENT/999/XYZ",  # Hallucinated!
    }

    result = verifier.verify_and_ground(extracted, doc)

    # 1. Grounded field retained
    assert "land_area_acres" in result.grounded_fields
    assert result.grounded_fields["land_area_acres"].value == 5.2

    # 2. Fabricated values must be discarded from grounded_fields
    assert "fabricated_land_area" not in result.grounded_fields
    assert "hallucinated_survey" not in result.grounded_fields

    # 3. Fabricated values must be placed into rejected_fields
    assert "fabricated_land_area" in result.rejected_fields
    assert result.rejected_fields["fabricated_land_area"] == 99.85
    assert "hallucinated_survey" in result.rejected_fields

    # 4. Reason must be explicitly "hallucination_rejected"
    assert result.rejection_reasons["fabricated_land_area"] == "hallucination_rejected"
    assert result.rejection_reasons["hallucinated_survey"] == "hallucination_rejected"

    # 5. Hallucination log entries recorded
    assert any("hallucination_rejected: field 'fabricated_land_area'" in log for log in result.hallucination_log)
    assert result.rejected_count == 2
    assert not result.is_fully_grounded


# ===========================================================================
# 3. DELIVERABLE 3: Fine-Tuning Scaffold
# ===========================================================================


def test_synthetic_dataset_builder_schema() -> None:
    """Dataset builder generates synthetic pairs with instruction, input, output, and ChatML messages."""
    record = generate_synthetic_record(seed=42)

    assert "instruction" in record
    assert "input" in record
    assert "output" in record
    assert "ground_truth" in record
    assert "messages" in record

    # Validate output parses as valid JSON
    parsed_out = json.loads(record["output"])
    gt = record["ground_truth"]
    assert parsed_out["land_area_acres"] == gt["land_area_acres"]
    assert parsed_out["survey_no"] == gt["survey_no"]
    assert parsed_out["fire_noc_expiry_date"] == gt["fire_noc_expiry_date"]

    # Validate ChatML messages structure for TRL SFTTrainer
    messages = record["messages"]
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"


def test_evaluate_script_exact_match_and_grounding_rate() -> None:
    """Evaluation script measures field-level exact match and grounding rate correctly."""
    samples = [
        # Sample 1: Perfect match & fully grounded
        {
            "input": "Land area is 4.5 acres. Survey: 10/2.",
            "ground_truth": {"land_area_acres": 4.5, "survey_no": "10/2"},
            "prediction": {"land_area_acres": 4.5, "survey_no": "10/2"},
        },
        # Sample 2: One match, one hallucination (not grounded in text)
        {
            "input": "Fire NOC valid until 2026-05-15.",
            "ground_truth": {"fire_noc_expiry_date": "2026-05-15", "total_faculty": 20},
            "prediction": {"fire_noc_expiry_date": "2026-05-15", "total_faculty": 99},  # 99 not in input!
        },
    ]

    metrics = evaluate_predictions(samples)
    summary = metrics["summary"]

    assert summary["total_target_fields"] == 4
    # 3 exact matches out of 4 (4.5, 10/2, 2026-05-15)
    assert summary["exact_matches"] == 3
    assert summary["field_exact_match_rate"] == 0.75

    # Total predicted fields: 4. Grounded: 3 ("4.5", "10/2", "2026-05-15"). Hallucinated: 1 ("99")
    assert summary["total_predicted_fields"] == 4
    assert summary["grounded_predicted_fields"] == 3
    assert summary["hallucination_count"] == 1
    assert summary["grounding_rate"] == 0.75
    assert summary["hallucination_rate"] == 0.25


def test_train_lora_safety_confirmation_guard() -> None:
    """Fine-tuning script verifies that training does NOT execute automatically without explicit confirmation."""
    import sys

    from training.train_lora import main as train_main

    orig_argv = sys.argv
    try:
        sys.argv = ["train_lora.py"]
        # SystemExit with code 0 indicates safe halt
        with pytest.raises(SystemExit) as exc:
            train_main()
        assert exc.value.code == 0
    finally:
        sys.argv = orig_argv


# ===========================================================================
# 4. DELIVERABLE 4: Lab Asset Counter
# ===========================================================================


def test_mock_lab_asset_detector(test_image: Path) -> None:
    """Mock detector generates synthetic workstation boxes with labels and confidences."""
    detector = MockLabAssetDetector(mock_count=18, default_confidence=0.94)
    detections = detector.detect(test_image)

    assert len(detections) == 18
    assert detections[0].label == "workstation"
    assert detections[0].confidence == 0.94
    assert detections[0].width > 0
    assert detections[0].height > 0


def test_annotate_image(test_image: Path, tmp_path: Path) -> None:
    """Image annotation renders bounding boxes and audit header banner."""
    out_annotated = tmp_path / "annotated.jpg"
    boxes = [
        DetectionBox(x1=50, y1=60, x2=150, y2=160, confidence=0.92, class_id=68, label="workstation"),
        DetectionBox(x1=200, y1=60, x2=300, y2=160, confidence=0.88, class_id=68, label="workstation"),
    ]

    result_path = annotate_image(test_image, boxes, out_annotated, title="Test Audit Banner")
    assert result_path.exists()
    assert result_path.stat().st_size > 0

    # Verify output is a valid JPEG
    with Image.open(result_path) as img:
        assert img.size == (640, 480)


def test_verify_lab_inventory_advisory_finding(test_image: Path, tmp_path: Path) -> None:
    """Lab inventory verification compares detected vs declared count and produces advisory Finding."""
    detector = MockLabAssetDetector(mock_count=20)
    declared = 25  # Deficit of 5 workstations

    result = verify_lab_inventory(
        image_path=test_image,
        declared_count=declared,
        detector=detector,
        rule_id="AICTE-2024-LAB-001",
        output_dir=tmp_path,
    )

    assert result.detected_count == 20
    assert result.declared_count == 25
    assert result.discrepancy == -5
    assert Path(result.annotated_image_path).exists()

    finding = result.finding
    assert finding.rule_id == "AICTE-2024-LAB-001"
    # Core Principle 1: Must be MANUAL_REVIEW_REQUIRED, is_model_advisory_only True
    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.is_model_advisory_only is True
    assert finding.highest_trust_level == TrustLevel.MODEL
    assert len(finding.evidence_list) == 1

    ev = finding.evidence_list[0]
    assert ev.trust_level == TrustLevel.MODEL
    assert ev.verification_method == "YOLOX_M_ONNX_ADVISORY"
    assert ev.raw_value["discrepancy"] == -5
    assert ev.is_decisive is False


def test_yolox_asset_detector_nms() -> None:
    """YOLOXAssetDetector NMS eliminates highly overlapping redundant boxes."""
    b1 = DetectionBox(x1=10, y1=10, x2=50, y2=50, confidence=0.95, class_id=68, label="monitor")
    b2 = DetectionBox(x1=12, y1=12, x2=50, y2=50, confidence=0.80, class_id=68, label="monitor")  # High overlap with b1
    b3 = DetectionBox(x1=100, y1=100, x2=150, y2=150, confidence=0.90, class_id=68, label="monitor")  # Distinct

    filtered = YOLOXAssetDetector._nms([b1, b2, b3], iou_threshold=0.5)
    assert len(filtered) == 2
    assert b1 in filtered
    assert b3 in filtered
    assert b2 not in filtered


# ===========================================================================
# 5. DELIVERABLE 5: "Ask Why" Assistant
# ===========================================================================


def test_ask_why_answers_in_context_question_with_citations(sample_finding: Finding) -> None:
    """Ask Why assistant answers questions regarding in-context rules/findings citing rule_id/clause/page."""
    rule = Rule(
        rule_id="AICTE-2024-LAND-001",
        title="Land Requirement for Technical Campuses",
        citation=RuleCitation(
            document="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 4.1",
            page=32,
            edition="2024-2027",
            table="Table 4.1",
        ),
        applicable_years=["2024-2025"],
        category="Land",
        severity=RuleSeverity.CRITICAL,
        logic="land_area_acres >= 5.0",
        parameters={"required_area": 5.0},
    )

    facts = {
        "land_area_acres": 3.2,
        "location_type": "Urban",
    }

    context = AskWhyContext(
        finding=sample_finding,
        rule=rule,
        facts=facts,
        evidence_items=sample_finding.evidence_list,
    )

    assistant = AskWhyAssistant(backend=StubAskWhyLLM())
    response = assistant.ask(
        question="Why did the land area rule fail for this institution?",
        context=context,
    )

    # Must NOT be a refusal
    assert not response.is_refusal
    assert "FAIL" in response.answer
    assert "3.2" in response.answer or "Clause 4.1" in response.answer

    # Must contain citations to rule_id, clause, and page
    assert len(response.citations) >= 1
    citation = response.citations[0]
    assert citation.rule_id == "AICTE-2024-LAND-001"
    assert "4.1" in citation.clause
    assert str(citation.page) == "32"
    assert response.trust_level == TrustLevel.MODEL


def test_ask_why_refuses_out_of_context_questions(sample_finding: Finding) -> None:
    """MANDATORY TEST: Ask Why refuses out-of-context questions and external knowledge."""
    context = AskWhyContext(
        finding=sample_finding,
        facts={"land_area_acres": 3.2},
    )

    assistant = AskWhyAssistant(backend=StubAskWhyLLM())

    out_of_context_queries = [
        "What is the weather in New Delhi today?",
        "Who is the president of France?",
        "What is the capital of Japan?",
        "What is the tuition fee for computer science?",
        "Can you write a poem about cricket?",
    ]

    for q in out_of_context_queries:
        resp = assistant.ask(question=q, context=context)
        # Must strictly refuse
        assert resp.is_refusal, f"Failed to refuse out-of-context query: '{q}'"
        assert resp.answer.startswith("REFUSAL:"), f"Expected refusal prefix for: '{q}'"
        assert len(resp.citations) == 0, f"Refusal should not provide regulatory citations for: '{q}'"


# ===========================================================================
# 6. FASTAPI ADVISORY API INTEGRATION TESTS
# ===========================================================================


def test_api_advisory_extract_and_ground() -> None:
    """POST /api/advisory/extract extracts structured fields and grounds them."""
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


def test_api_advisory_asset_count(test_image: Path) -> None:
    """POST /api/advisory/asset-count processes lab photo and returns advisory Finding."""
    client = TestClient(app)
    with test_image.open("rb") as f:
        files = {"file": ("lab.jpg", f, "image/jpeg")}
        data = {"declared_count": "30", "use_mock": "true"}
        response = client.post("/api/advisory/asset-count", files=files, data=data)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["detected_count"] == 20
    assert res_data["declared_count"] == 30
    assert res_data["discrepancy"] == -10
    assert "annotated_image_path" in res_data
    assert res_data["finding"]["status"] == "MANUAL_REVIEW_REQUIRED"
    assert res_data["finding"]["is_model_advisory_only"] is True


def test_api_advisory_ask_why(sample_finding: Finding) -> None:
    """POST /api/advisory/ask-why responds with citation or refusal."""
    client = TestClient(app)
    # 1. In-context query
    payload = {
        "question": "Why did this land area finding fail?",
        "finding": sample_finding.model_dump(mode="json"),
        "facts": {"land_area_acres": 3.2},
    }
    resp = client.post("/api/advisory/ask-why", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert not data["is_refusal"]
    assert len(data["citations"]) >= 1

    # 2. Out-of-context query
    payload_ooc = {
        "question": "What is the weather forecast?",
        "finding": sample_finding.model_dump(mode="json"),
        "facts": {"land_area_acres": 3.2},
    }
    resp_ooc = client.post("/api/advisory/ask-why", json=payload_ooc)
    assert resp_ooc.status_code == 200
    data_ooc = resp_ooc.json()
    assert data_ooc["is_refusal"]
    assert "REFUSAL:" in data_ooc["answer"]
