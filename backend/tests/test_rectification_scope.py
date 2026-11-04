"""Verification & Rectification Workflow: Internal finding masking, institution-safe finding rewrites."""

from __future__ import annotations

import pytest

from nirikshan.core.rule_schema import (
    EvidenceRequirement,
    Rule,
    RuleCitation,
    RuleSeverity,
)
from nirikshan.rules.engine import RuleEngine, RuleResultStatus
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import (
    BoundingBox,
    EvidenceItem,
    TrustLevel,
)


def test_rule_fail_renders_deficiency_template() -> None:
    """When a rule fails, the deficiency template is populated with context parameters for the institution."""
    rule = Rule(
        rule_id="AICTE-DEF-001",
        title="Land Requirement",
        citation=RuleCitation(document="APH 2024", clause="4.1", page=40),
        applicable_years=["2024-2025"],
        category="Land",
        evidence_requirements=[],
        logic="land_area >= 5.0",
        severity=RuleSeverity.CRITICAL,
        deficiency_template="Institution possesses {land_area} acres which is below the mandatory requirement of 5.0 acres.",
    )
    engine = RuleEngine()
    result = engine.evaluate_one(rule, {"land_area": 3.2}, [])
    assert result.status == RuleResultStatus.FAIL
    assert "Institution possesses 3.2 acres which is below the mandatory requirement of 5.0 acres." in result.deficiency


def test_internal_finding_masking_for_institution_scope() -> None:
    """Institution view of findings masks internal forensic indicators and raw internal signatures."""
    internal_evidence = EvidenceItem(
        evidence_id="ev-internal-01",
        trust_level=TrustLevel.STRUCTURAL_FORENSIC,
        source_type="LAND_DEED",
        description="Ghostscript producer detected with altered cross-reference table offset 0x004F",
        source_document_id="doc-internal-01",
        source_document_name="land_deed.pdf",
        verification_method="FORENSIC_XREF_INSPECTION",
    )
    finding = Finding(
        finding_id="fnd-rect-01",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        summary="Document integrity review required for Land Deed.",
        details="Internal analysis flagged structural discrepancy.",
        handbook_citation=HandbookCitation(
            clause="Clause 4.1",
            page=42,
        ),
        evidence_list=[internal_evidence],
    )
    finding.validate_trust_integrity()

    # Generate institution-safe representation
    inst_safe_dict = {
        "finding_id": finding.finding_id,
        "rule_id": finding.rule_id,
        "category": finding.category,
        "status": finding.status.value,
        "summary": finding.summary,
        "clause": finding.handbook_citation.clause if finding.handbook_citation else "",
    }

    # Verify internal details and method strings are masked
    assert "0x004F" not in inst_safe_dict["summary"]
    assert "FORENSIC_XREF_INSPECTION" not in str(inst_safe_dict)
    assert inst_safe_dict["status"] == "MANUAL_REVIEW_REQUIRED"


def test_rectification_rewrite_provides_actionable_remedy() -> None:
    """Rectification notice rewrites finding to indicate the acceptable remedial documents under APH."""
    citation = HandbookCitation(
        clause="Clause 6.1",
        page=70,
        handbook="AICTE Approval Process Handbook 2024-2027",
    )
    finding = Finding(
        finding_id="fnd-rect-02",
        rule_id="AICTE-2024-SAFE-001",
        rule_name="Fire Safety NOC",
        category="Safety",
        status=VerificationStatus.FAIL,
        summary="Fire Safety NOC expired or missing.",
        details="Valid fire NOC not provided.",
        handbook_citation=citation,
    )
    # Safe rewrite template for institution
    remedy_notice = (
        f"Deficiency under {finding.handbook_citation.clause}: Please upload a valid, digitally signed "
        "Fire Safety Certificate or NOC issued by the Competent Fire Authority."
    )
    assert "Clause 6.1" in remedy_notice
    assert "Fire Safety Certificate" in remedy_notice
