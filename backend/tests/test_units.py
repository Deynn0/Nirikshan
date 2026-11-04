"""Core Pipeline & Foundation: Unit tests.

Covers:
- AST expressions & safe evaluator (comparisons, arithmetic, date math, code injection blocking)
- Provenance & Trust Ladder axioms (strict ordering, advisory-only models, unverified self-attestations)
- PDF tampering signals & forensic escalation
- PKI roots and certificate chain verification
"""

from __future__ import annotations

import datetime
from datetime import date, timedelta
from pathlib import Path

import asn1crypto.x509 as asn1_x509
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pyhanko_certvalidator.registry import SimpleCertificateStore

from nirikshan.core.rule_schema import (
    EvidenceRequirement,
    Rule,
    RuleCitation,
    RuleSeverity,
)
from nirikshan.core.safe_eval import SafeASTEvaluator, SafeEvalError
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.rules.engine import RuleEngine, RuleResultStatus
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport
from nirikshan.trust.ladder import (
    TRUST_RANKS,
    BoundingBox,
    EvidenceItem,
    TrustLevel,
)


def _create_evidence(
    doc_type: str,
    trust_level: TrustLevel,
    is_self_attested: bool = False,
    is_tampered: bool = False,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id="ev-001",
        trust_level=trust_level,
        source_type=doc_type,
        description="Test evidence item",
        source_document_id="doc-001",
        source_document_name="test.pdf",
        verification_method="TEST_VERIFIER",
        is_self_attested=is_self_attested,
        is_tampered=is_tampered,
    )


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


# ---------------------------------------------------------------------------
# AST Expressions & Safe Evaluator
# ---------------------------------------------------------------------------

def test_safe_eval_comparisons_and_arithmetic() -> None:
    evaluator = SafeASTEvaluator()
    facts = {
        "land_area": 3.5,
        "min_area": 2.5,
        "is_contiguous": True,
        "category": "Urban",
        "roles": ["UG", "PG"],
    }

    assert evaluator.evaluate("land_area >= min_area and is_contiguous == True", facts) is True
    assert evaluator.evaluate("land_area < 2.0 or not is_contiguous", facts) is False
    assert evaluator.evaluate("category in ['Urban', 'Metro']", facts) is True
    assert evaluator.evaluate("category not in ['Rural']", facts) is True
    assert evaluator.evaluate("10 * 2 + 5 == 25", facts) is True


def test_safe_eval_date_arithmetic() -> None:
    evaluator = SafeASTEvaluator()
    future = (date.today() + timedelta(days=100)).strftime("%Y-%m-%d")
    past = (date.today() - timedelta(days=100)).strftime("%Y-%m-%d")

    assert evaluator.evaluate(f"days_until('{future}') > 0", {}) is True
    assert evaluator.evaluate(f"days_until('{past}') < 0", {}) is True
    assert evaluator.evaluate("date_diff('2025-01-01', '2025-01-11', 'days') == 10", {}) is True


def test_safe_evaluator_blocks_code_injection() -> None:
    evaluator = SafeASTEvaluator()
    with pytest.raises((SafeEvalError, ValueError)):
        evaluator.evaluate("__import__('os').system('dir')", {})

    with pytest.raises((SafeEvalError, ValueError)):
        evaluator.evaluate("open('secret.txt').read()", {})

    with pytest.raises((SafeEvalError, ValueError)):
        evaluator.evaluate("lambda x: x", {})


# ---------------------------------------------------------------------------
# Provenance & Trust Ladder Axioms
# ---------------------------------------------------------------------------

def test_trust_ladder_strict_ordering() -> None:
    assert TRUST_RANKS[TrustLevel.CRYPTOGRAPHIC] > TRUST_RANKS[TrustLevel.ISSUER]
    assert TRUST_RANKS[TrustLevel.ISSUER] > TRUST_RANKS[TrustLevel.RECORD]
    assert TRUST_RANKS[TrustLevel.RECORD] > TRUST_RANKS[TrustLevel.RULE]
    assert TRUST_RANKS[TrustLevel.RULE] > TRUST_RANKS[TrustLevel.STRUCTURAL_FORENSIC]
    assert TRUST_RANKS[TrustLevel.STRUCTURAL_FORENSIC] > TRUST_RANKS[TrustLevel.MODEL]
    assert TRUST_RANKS[TrustLevel.MODEL] > TRUST_RANKS[TrustLevel.UNVERIFIED_CLAIM]


def test_applicant_self_attestation_never_verified() -> None:
    evidence = EvidenceItem(
        evidence_id="ev-claim-001",
        trust_level=TrustLevel.RECORD,
        source_type="AFFIDAVIT_SELF_DECLARATION",
        description="Affidavit stating campus possesses 5 acres of land",
        source_document_id="doc-affidavit-1",
        source_document_name="self_declaration_affidavit.pdf",
        is_self_attested=True,
        verification_method="NOTARY_AFFIDAVIT_ONLY",
    )
    assert evidence.effective_trust_level() == TrustLevel.UNVERIFIED_CLAIM
    assert evidence.is_decisive is False


def test_model_output_is_advisory_only_cannot_decide_pass_or_fail() -> None:
    bbox = BoundingBox(page=1, x=50.0, y=100.0, width=200.0, height=40.0)
    model_evidence = EvidenceItem(
        evidence_id="ev-model-001",
        trust_level=TrustLevel.MODEL,
        source_type="OCR_VISION_PREDICTION",
        description="OCR model detected 5.2 acres text",
        raw_value=5.2,
        source_document_id="doc-scan-1",
        source_document_name="unverified_scan.pdf",
        bounding_box=bbox,
        verification_method="OCR_HEURISTIC_PREDICTOR",
    )

    finding = Finding(
        finding_id="fnd-test-01",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.PASS,
        summary="Passed via OCR prediction",
        details="Clause 4.1",
        handbook_citation=HandbookCitation(
            handbook="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 4.1",
            page=42,
            edition="2024-2027",
        ),
        evidence_list=[model_evidence],
    )
    finding.validate_trust_integrity()
    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.is_model_advisory_only is True


def test_self_attestation_collapses_trust_gate_blocks_pass() -> None:
    rule = Rule(
        rule_id="AICTE-GATE-ATTEST",
        title="Fire NOC Rule",
        citation=RuleCitation(document="Doc", clause="1", page=1),
        applicable_years=["2024-2025"],
        category="Safety",
        evidence_requirements=[
            EvidenceRequirement(type="FIRE_SAFETY_NOC", min_trust_level="ISSUER")
        ],
        logic="fire_noc_valid == True",
    )
    engine = RuleEngine()
    ev_attested = _create_evidence("FIRE_SAFETY_NOC", TrustLevel.ISSUER, is_self_attested=True)
    result = engine.evaluate_one(rule, {"fire_noc_valid": True}, [ev_attested])
    assert result.status == RuleResultStatus.UNVERIFIED


def test_trust_gate_allows_pass_when_trust_satisfied() -> None:
    rule = Rule(
        rule_id="AICTE-GATE-PASS",
        title="Fire NOC Rule",
        citation=RuleCitation(document="Doc", clause="1", page=1),
        applicable_years=["2024-2025"],
        category="Safety",
        evidence_requirements=[
            EvidenceRequirement(type="FIRE_SAFETY_NOC", min_trust_level="ISSUER")
        ],
        logic="fire_noc_valid == True",
    )
    engine = RuleEngine()
    ev = [_create_evidence("FIRE_SAFETY_NOC", TrustLevel.ISSUER)]
    result = engine.evaluate_one(rule, {"fire_noc_valid": True}, ev)
    assert result.status == RuleResultStatus.PASS
    assert result.logic_result is True


# ---------------------------------------------------------------------------
# PDF Tampering Signals
# ---------------------------------------------------------------------------

def test_tampered_document_triggers_tamper_flag() -> None:
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
    findings = rule_engine.evaluate_dossier(
        dossier,
        docs,
        {
            "land_area_acres": 3.5,
            "survey_no_deed": "101/2",
            "survey_no_conversion": "404/9",
        },
    )
    survey_finding = next(f for f in findings if f.rule_id == "AICTE-RECON-SURVEY-001")
    assert survey_finding.status == VerificationStatus.FAIL


# ---------------------------------------------------------------------------
# PKI Roots Verification
# ---------------------------------------------------------------------------

def test_pki() -> None:
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AICTE Root CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "AICTE Scrutiny Root CA"),
    ])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    der_bytes = ca_cert.public_bytes(serialization.Encoding.DER)
    asn1_cert = asn1_x509.Certificate.load(der_bytes)
    store = SimpleCertificateStore()
    store.register(asn1_cert)
    assert len(list(store)) == 1
