"""Insight Engine: Application readiness & completeness scoring."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from starlette.testclient import TestClient

from nirikshan.advisory.asset_counter import (
    DetectionBox,
    MockLabAssetDetector,
    YOLOXAssetDetector,
    annotate_image,
    verify_lab_inventory,
)
from nirikshan.main import app
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import VerificationStatus
from nirikshan.schemas.forensic import DocumentType
from nirikshan.trust.ladder import TrustLevel


@pytest.fixture
def test_image(tmp_path: Path) -> Path:
    img_path = tmp_path / "lab_sample.jpg"
    img = Image.new("RGB", (640, 480), color=(180, 200, 220))
    img.save(img_path, format="JPEG")
    return img_path


# ---------------------------------------------------------------------------
# Lab Asset Counter & Inventory Verification
# ---------------------------------------------------------------------------

def test_mock_lab_asset_detector(test_image: Path) -> None:
    detector = MockLabAssetDetector(mock_count=18, default_confidence=0.94)
    detections = detector.detect(test_image)

    assert len(detections) == 18
    assert detections[0].label == "workstation"
    assert detections[0].confidence == 0.94
    assert detections[0].width > 0
    assert detections[0].height > 0


def test_annotate_image(test_image: Path, tmp_path: Path) -> None:
    out_annotated = tmp_path / "annotated.jpg"
    boxes = [
        DetectionBox(x1=50, y1=60, x2=150, y2=160, confidence=0.92, class_id=68, label="workstation"),
        DetectionBox(x1=200, y1=60, x2=300, y2=160, confidence=0.88, class_id=68, label="workstation"),
    ]
    result_path = annotate_image(test_image, boxes, out_annotated, title="Test Audit Banner")
    assert result_path.exists()
    assert result_path.stat().st_size > 0


def test_verify_lab_inventory_advisory_finding(test_image: Path, tmp_path: Path) -> None:
    detector = MockLabAssetDetector(mock_count=20)
    declared = 25

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

    finding = result.finding
    assert finding.rule_id == "AICTE-2024-LAB-001"
    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.is_model_advisory_only is True


def test_yolox_asset_detector_nms() -> None:
    b1 = DetectionBox(x1=10, y1=10, x2=50, y2=50, confidence=0.95, class_id=68, label="monitor")
    b2 = DetectionBox(x1=12, y1=12, x2=50, y2=50, confidence=0.80, class_id=68, label="monitor")
    b3 = DetectionBox(x1=100, y1=100, x2=150, y2=150, confidence=0.90, class_id=68, label="monitor")

    filtered = YOLOXAssetDetector._nms([b1, b2, b3], iou_threshold=0.5)
    assert len(filtered) == 2
    assert b1 in filtered
    assert b3 in filtered
    assert b2 not in filtered


def test_api_advisory_asset_count(test_image: Path) -> None:
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
    assert res_data["finding"]["status"] == "MANUAL_REVIEW_REQUIRED"


# ---------------------------------------------------------------------------
# Application Readiness & Completeness Scoring
# ---------------------------------------------------------------------------

def test_application_readiness_scoring_algorithm() -> None:
    """Calculate application readiness score based on presence of mandatory statutory documents."""
    mandatory_docs = [
        DocumentType.LAND_SALE_DEED,
        DocumentType.LAND_USE_CONVERSION_CERT,
        DocumentType.BUILDING_PLAN_APPROVED,
        DocumentType.FIRE_SAFETY_NOC,
    ]

    # Case 1: All mandatory documents present -> 100% readiness
    provided_case_full = [
        DocumentType.LAND_SALE_DEED,
        DocumentType.LAND_USE_CONVERSION_CERT,
        DocumentType.BUILDING_PLAN_APPROVED,
        DocumentType.FIRE_SAFETY_NOC,
    ]
    present_count = sum(1 for d in mandatory_docs if d in provided_case_full)
    readiness_score = (present_count / len(mandatory_docs)) * 100.0
    assert readiness_score == 100.0

    # Case 2: Missing Fire NOC -> 75% readiness with deficiency list
    provided_case_partial = [
        DocumentType.LAND_SALE_DEED,
        DocumentType.LAND_USE_CONVERSION_CERT,
        DocumentType.BUILDING_PLAN_APPROVED,
    ]
    missing = [d.value for d in mandatory_docs if d not in provided_case_partial]
    assert missing == ["FIRE_SAFETY_NOC"]
    partial_score = (len(provided_case_partial) / len(mandatory_docs)) * 100.0
    assert partial_score == 75.0

