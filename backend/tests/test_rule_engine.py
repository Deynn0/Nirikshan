"""Tests for deterministic AICTE Approval Process Handbook rule engine."""

from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport
from nirikshan.trust.ladder import TrustLevel


def _make_mock_doc(
    doc_id: str, doc_type: DocumentType, is_tampered: bool = False
) -> DocumentRecord:
    return DocumentRecord(
        document_id=doc_id,
        dossier_id="dos-test-01",
        file_name=f"{doc_type.value.lower()}.pdf",
        doc_type=doc_type,
        title=f"Sample {doc_type.value}",
        page_count=2,
        forensic=ForensicReport(
            document_id=doc_id,
            file_name=f"{doc_type.value.lower()}.pdf",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size_bytes=10240,
            page_count=2,
            is_tampered=is_tampered,
            tamper_flags=["Inconsistent Creation Date"] if is_tampered else [],
            has_digital_signature=not is_tampered,
            signature_valid=not is_tampered,
            assessed_trust_level=TrustLevel.STRUCTURAL_FORENSIC
            if is_tampered
            else TrustLevel.CRYPTOGRAPHIC,
        ),
        extracted_text_preview="Sample verified text",
    )


def test_land_area_evaluation_urban_pass_and_fail() -> None:
    """Urban UG Technical institution mandates 2.5 Acres."""
    dossier = ApplicationDossier(
        dossier_id="dos-test-01",
        institution_name="Nirikshan Institute of Technology",
        application_number="AICTE/2024/NIT/001",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
    )
    docs = [_make_mock_doc("doc-deed-1", DocumentType.LAND_SALE_DEED)]

    # 1. Test passing case (3.0 Acres >= 2.5 required)
    findings_pass = rule_engine.evaluate_dossier(
        dossier, docs, {"land_area_acres": 3.0, "is_contiguous": True}
    )
    land_finding = next(f for f in findings_pass if f.rule_id == "AICTE-2024-LAND-001")
    assert land_finding.status == VerificationStatus.PASS
    assert land_finding.handbook_citation.clause == "Clause 4.1"
    assert land_finding.handbook_citation.page == 42
    assert land_finding.primary_bounding_box is not None

    # 2. Test shortfall case (2.0 Acres < 2.5 required)
    findings_fail = rule_engine.evaluate_dossier(
        dossier, docs, {"land_area_acres": 2.0, "is_contiguous": True}
    )
    land_finding_fail = next(f for f in findings_fail if f.rule_id == "AICTE-2024-LAND-001")
    assert land_finding_fail.status == VerificationStatus.FAIL
    assert "Deficient: Possesses 2.0 Acres" in land_finding_fail.summary


def test_tampered_document_triggers_tamper_flag() -> None:
    """Document with structural tampering must trigger FLAGGED_TAMPER finding."""
    dossier = ApplicationDossier(
        dossier_id="dos-test-02",
        institution_name="Tampered Tech Academy",
        application_number="AICTE/2024/TAMPER/001",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
    )
    tampered_doc = _make_mock_doc("doc-tampered-1", DocumentType.LAND_SALE_DEED, is_tampered=True)
    findings = rule_engine.evaluate_dossier(dossier, [tampered_doc], {"land_area_acres": 5.0})

    land_finding = next(f for f in findings if f.rule_id == "AICTE-2024-LAND-001")
    assert land_finding.status == VerificationStatus.FLAGGED_TAMPER
    assert any("tamper" in f.summary.lower() for f in findings)


def test_cross_document_survey_number_mismatch_detected() -> None:
    """Survey numbers mismatching between Land Deed and Conversion Order must produce anomaly."""
    dossier = ApplicationDossier(
        dossier_id="dos-test-03",
        institution_name="Survey Discrepancy College",
        application_number="AICTE/2024/SURV/001",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
    )
    docs = [
        _make_mock_doc("doc-deed-1", DocumentType.LAND_SALE_DEED),
        _make_mock_doc("doc-conv-1", DocumentType.LAND_USE_CONVERSION_CERT),
    ]
    # Mismatch: Deed has Survey #101/2, Conversion has Survey #404/9
    params = {
        "land_area_acres": 3.5,
        "survey_no_deed": "101/2",
        "survey_no_conversion": "404/9",
    }
    findings = rule_engine.evaluate_dossier(dossier, docs, params)
    recon_finding = next(f for f in findings if f.rule_id == "AICTE-RECON-SURVEY-001")
    assert recon_finding.status == VerificationStatus.FAIL
    assert "CRITICAL DISCREPANCY" in recon_finding.summary


def test_todo_citation_flag_preserved() -> None:
    """Handbook references with unknown text or draft rules must have needs_verification: true."""
    dossier = ApplicationDossier(
        dossier_id="dos-test-04",
        institution_name="Satellite Tech",
        application_number="AICTE/2024/SAT/001",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
    )
    findings = rule_engine.evaluate_dossier(dossier, [], {})
    todo_finding = next(f for f in findings if f.rule_id == "AICTE-2024-EXP-TODO")
    assert todo_finding.needs_verification is True
    assert todo_finding.handbook_citation.needs_verification is True
    assert todo_finding.handbook_citation.page == "TODO"
