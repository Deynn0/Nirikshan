"""Regulatory Governance & EC Handoff: AICTE Approval Process Handbook (APH) clause mapping & citations."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nirikshan.core.rule_schema import (
    EvidenceRequirement,
    Rule,
    RuleCitation,
    RuleSeverity,
)
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.rules.loader import RulesetLoader
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport
from nirikshan.trust.ladder import TrustLevel


def _make_mock_doc(doc_id: str, doc_type: DocumentType) -> DocumentRecord:
    return DocumentRecord(
        document_id=doc_id,
        dossier_id="dos-reg-01",
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
            is_tampered=False,
            has_digital_signature=True,
            signature_valid=True,
            assessed_trust_level=TrustLevel.CRYPTOGRAPHIC,
        ),
        extracted_text_preview="Sample verified text",
    )


# ---------------------------------------------------------------------------
# AICTE APH Ruleset Loading & SHA-256 Hash Integrity
# ---------------------------------------------------------------------------

def test_ruleset_loader_loads_sample_and_computes_sha256() -> None:
    loader = RulesetLoader()
    meta = loader.load("aicte_aph_sample.yaml")
    assert len(meta.rules) >= 10
    assert len(meta.sha256_hash) == 64
    assert all(c in "0123456789abcdef" for c in meta.sha256_hash)
    assert meta.version == "2024-2027-sample"


def test_ruleset_year_filtering() -> None:
    loader = RulesetLoader()
    rules_2025 = loader.filter_by_year("aicte_aph_sample.yaml", "2025-2026")
    assert len(rules_2025) >= 10
    rules_none = loader.filter_by_year("aicte_aph_sample.yaml", "1990-1991")
    assert len(rules_none) == 0


# ---------------------------------------------------------------------------
# Rule Schema Validation & Citation Mapping
# ---------------------------------------------------------------------------

def test_rule_schema_valid_instantiation() -> None:
    rule = Rule(
        rule_id="AICTE-TEST-001",
        title="Test Fire Safety Rule",
        citation=RuleCitation(
            document="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 6.1",
            page=60,
            edition="2024-2027",
            needs_verification=False,
        ),
        applicable_years=["2024-2025", "2025-2026"],
        category="Safety & Compliance",
        evidence_requirements=[
            EvidenceRequirement(type="FIRE_SAFETY_NOC", min_trust_level="ISSUER")
        ],
        logic="fire_noc_valid == True",
        severity=RuleSeverity.CRITICAL,
        deficiency_template="Fire NOC invalid: {fire_noc_valid}",
        needs_verification=False,
    )
    assert rule.rule_id == "AICTE-TEST-001"
    assert rule.severity == RuleSeverity.CRITICAL
    assert "Clause 6.1" in rule.display_citation
    assert "p.60" in rule.display_citation


def test_rule_schema_invalid_id_raises() -> None:
    with pytest.raises(ValidationError):
        Rule(
            rule_id="lower_case_id_not_allowed!",
            title="Bad Rule",
            citation=RuleCitation(document="Doc", clause="1", page=1),
            applicable_years=["2024-2025"],
            category="Test",
        )


def test_rule_schema_invalid_trust_level_raises() -> None:
    with pytest.raises(ValidationError):
        EvidenceRequirement(type="DOC_X", min_trust_level="SUPER_TRUST")


def test_citation_needs_verification_escalates_to_rule() -> None:
    rule = Rule(
        rule_id="AICTE-TODO-001",
        title="Draft Rule with Placeholder Citation",
        citation=RuleCitation(
            document="AICTE Handbook (Draft)",
            clause="Clause 99.9",
            page="TODO",
            needs_verification=True,
        ),
        applicable_years=["2024-2025"],
        category="Draft",
        needs_verification=False,
    )
    assert rule.needs_verification is True


def test_todo_citation_flag_preserved() -> None:
    dossier = ApplicationDossier(
        dossier_id="dos-test-04",
        institution_name="Pending Citation Academy",
        application_number="AICTE/2024/TODO/001",
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


# ---------------------------------------------------------------------------
# Deterministic AICTE APH Norms Evaluation (Land Area)
# ---------------------------------------------------------------------------

def test_land_area_evaluation_urban_pass_and_fail() -> None:
    dossier = ApplicationDossier(
        dossier_id="dos-reg-land",
        institution_name="Nirikshan Institute of Technology",
        application_number="AICTE/2024/NIT/001",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
    )
    docs = [_make_mock_doc("doc-deed-1", DocumentType.LAND_SALE_DEED)]

    # 1. Pass: 3.0 Acres >= 2.5 required
    findings_pass = rule_engine.evaluate_dossier(
        dossier, docs, {"land_area_acres": 3.0, "is_contiguous": True}
    )
    land_finding = next(f for f in findings_pass if f.rule_id == "AICTE-2024-LAND-001")
    assert land_finding.status == VerificationStatus.PASS
    assert land_finding.handbook_citation.clause == "Clause 4.1"

    # 2. Shortfall: 2.0 Acres < 2.5 required
    findings_fail = rule_engine.evaluate_dossier(
        dossier, docs, {"land_area_acres": 2.0, "is_contiguous": True}
    )
    land_finding_fail = next(f for f in findings_fail if f.rule_id == "AICTE-2024-LAND-001")
    assert land_finding_fail.status == VerificationStatus.FAIL
    assert "Deficient" in land_finding_fail.summary
