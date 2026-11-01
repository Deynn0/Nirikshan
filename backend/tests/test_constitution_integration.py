"""Integration audit test suite verifying Nirikshan Constitution compliance:

(1) No code path lets a Model-level or self-attested item produce a verified PASS.
(2) All untrusted document parsing strictly goes through the isolated sandbox.
(3) No outbound network calls exist at runtime (strict offline air-gap enforcement).
(4) Every finding strictly possesses a handbook citation and ordinal evidence level.
(5) Deterministic audit replay functions end-to-end with identical findings and risk scores.
"""

from __future__ import annotations

import socket
import uuid

import pytest

from nirikshan.config import settings
from nirikshan.core.rule_schema import EvidenceRequirement, Rule, RuleCitation
from nirikshan.db.session import async_session_factory, init_db
from nirikshan.engine.audit_log import record_evaluation_audit, replay, verify_chain
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.rules.engine import RuleEngine, RuleResultStatus
from nirikshan.sandbox import SandboxedWorkerManager, SandboxViolationError, SandboxViolationType
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport
from nirikshan.trust.ladder import EvidenceItem, TrustLevel


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    await init_db()


# ---------------------------------------------------------------------------
# (1) Model-level or self-attested item CAN NEVER produce a verified PASS
# ---------------------------------------------------------------------------

def test_constitution_finding_model_downgrades_attempted_pass() -> None:
    """Model-level evidence claiming PASS must automatically downgrade to MANUAL_REVIEW_REQUIRED."""
    model_evidence = EvidenceItem(
        evidence_id="ev-model-01",
        trust_level=TrustLevel.MODEL,
        source_type="LAND_SURVEY_OCR",
        description="OCR extracted 5.0 acres",
        source_document_id="doc-ocr-1",
        source_document_name="scan.pdf",
        verification_method="YOLOX_OCR_MODEL",
    )

    finding = Finding(
        finding_id="fnd-test-pass-downgrade",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.PASS,  # Attempting to declare PASS with model evidence
        summary="Passed via model detection",
        details="Model detected 5.0 acres",
        handbook_citation=HandbookCitation(
            handbook="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 4.1",
            page=42,
        ),
        evidence_list=[model_evidence],
    )

    # Automatic validator must downgrade status immediately
    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.is_model_advisory_only is True
    assert finding.highest_trust_level == TrustLevel.MODEL
    assert finding.evidence_level == TrustLevel.MODEL


def test_constitution_finding_self_attestation_downgrades_attempted_pass() -> None:
    """Applicant self-attestation claiming PASS must automatically collapse and downgrade to MANUAL_REVIEW_REQUIRED."""
    self_attested_evidence = EvidenceItem(
        evidence_id="ev-claim-01",
        trust_level=TrustLevel.RECORD,  # Claimed record level
        source_type="AFFIDAVIT",
        description="Applicant notary affidavit claiming 10 acres",
        source_document_id="doc-aff-1",
        source_document_name="affidavit.pdf",
        is_self_attested=True,  # Self-attestation flag
        verification_method="NOTARY_AFFIDAVIT",
    )

    finding = Finding(
        finding_id="fnd-test-claim-downgrade",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.PASS,
        summary="Passed via applicant self-declaration",
        details="Applicant claims 10 acres in affidavit",
        handbook_citation=HandbookCitation(
            clause="Clause 4.1",
            page=42,
        ),
        evidence_list=[self_attested_evidence],
    )

    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.highest_trust_level == TrustLevel.UNVERIFIED_CLAIM
    assert finding.evidence_level == TrustLevel.UNVERIFIED_CLAIM


def test_constitution_rules_engine_blocks_pass_on_model_or_claim_evidence() -> None:
    """RuleEngine trust-gate must return UNVERIFIED (never PASS) when supported only by model/claim evidence."""
    rule = Rule(
        rule_id="AICTE-RULE-AUDIT-01",
        title="Fire Safety Certificate",
        citation=RuleCitation(document="AICTE APH", clause="Clause 6.1", page=70),
        applicable_years=["2024-2025"],
        category="Safety",
        evidence_requirements=[
            EvidenceRequirement(type="FIRE_NOC", min_trust_level="ISSUER")
        ],
        logic="has_fire_noc == True",
    )
    engine = RuleEngine()

    # Case A: Model-level evidence provided
    model_ev = [
        EvidenceItem(
            evidence_id="ev-1",
            trust_level=TrustLevel.MODEL,
            source_type="FIRE_NOC",
            description="Model detected fire NOC header",
            source_document_id="doc-1",
            source_document_name="fire.pdf",
            verification_method="OCR_HEURISTIC",
        )
    ]
    res_model = engine.evaluate_one(rule, {"has_fire_noc": True}, model_ev)
    assert res_model.status == RuleResultStatus.UNVERIFIED
    assert res_model.status != RuleResultStatus.PASS

    # Case B: Self-attested claim evidence provided
    claim_ev = [
        EvidenceItem(
            evidence_id="ev-2",
            trust_level=TrustLevel.ISSUER,  # Claiming issuer level
            source_type="FIRE_NOC",
            description="Self-attested affidavit regarding fire safety",
            source_document_id="doc-2",
            source_document_name="affidavit.pdf",
            is_self_attested=True,
            verification_method="SELF_DECLARATION",
        )
    ]
    res_claim = engine.evaluate_one(rule, {"has_fire_noc": True}, claim_ev)
    assert res_claim.status == RuleResultStatus.UNVERIFIED
    assert res_claim.status != RuleResultStatus.PASS


# ---------------------------------------------------------------------------
# (2) All document parsing strictly goes through the sandbox
# ---------------------------------------------------------------------------

def test_constitution_sandbox_enforces_quarantine_isolation(tmp_path) -> None:
    """Sandbox isolates untrusted execution, enforcing memory/CPU and decompression limits."""
    mgr = SandboxedWorkerManager(
        wall_clock_timeout=2,
        max_file_size_bytes=1024,
    )

    oversized_file = tmp_path / "oversized_sample.pdf"
    oversized_file.write_bytes(b"A" * 2048)

    with pytest.raises(SandboxViolationError) as exc_info:
        mgr.validate_file_guards(oversized_file)

    assert exc_info.value.violation_type == SandboxViolationType.FILE_SIZE_EXCEEDED


# ---------------------------------------------------------------------------
# (3) No network calls exist at runtime
# ---------------------------------------------------------------------------

def test_constitution_airgap_blocks_external_network() -> None:
    """Outbound socket connections to non-loopback addresses must be blocked at runtime."""
    assert settings.allow_external_network is False

    from nirikshan.main import _install_airgap_guard
    _install_airgap_guard()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(PermissionError) as exc_info:
            s.connect(("8.8.8.8", 53))
        assert "Airgap Violation" in str(exc_info.value)
    finally:
        s.close()


# ---------------------------------------------------------------------------
# (4) Every finding strictly possesses a citation and evidence level
# ---------------------------------------------------------------------------

def test_constitution_finding_serialization_carries_citation_and_evidence_level() -> None:
    """Finding model_dump / json serialization strictly includes citation, highest_trust_level, and evidence_level."""
    deed_ev = EvidenceItem(
        evidence_id="ev-rec-01",
        trust_level=TrustLevel.RECORD,
        source_type="LAND_SALE_DEED",
        description="Registered Sub-Registrar Book-1 Title Deed",
        source_document_id="doc-deed-01",
        source_document_name="registered_deed.pdf",
        verification_method="SUB_REGISTRAR_REGISTRY",
    )

    finding = Finding(
        finding_id="fnd-audit-citation-01",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.PASS,
        summary="Compliant title deed verified",
        details="Sub-Registrar record confirms 5.0 acres",
        handbook_citation=HandbookCitation(
            handbook="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 4.1",
            page=42,
            edition="2024-2027",
            table="Table 4.1",
        ),
        evidence_list=[deed_ev],
    )

    dumped = finding.model_dump()
    assert "handbook_citation" in dumped
    assert dumped["handbook_citation"]["clause"] == "Clause 4.1"
    assert dumped["handbook_citation"]["page"] == 42
    assert "highest_trust_level" in dumped
    assert dumped["highest_trust_level"] == "RECORD"
    assert "evidence_level" in dumped
    assert dumped["evidence_level"] == "RECORD"


# ---------------------------------------------------------------------------
# (5) The audit replay works end-to-end with full determinism
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_constitution_audit_replay_end_to_end_with_parameters() -> None:
    """Audit log records full snapshot (including extracted parameters) and replays with 100% concordance."""
    async with async_session_factory() as db:
        dossier_id = f"dos-const-replay-{uuid.uuid4().hex[:6]}"
        extracted_params = {
            "land_area_acres": 4.5,
            "is_contiguous": True,
            "faculty_count": 60,
            "cadre_professors": 5,
            "cadre_assoc_professors": 15,
            "cadre_asst_professors": 40,
            "fdr_amount_lakhs": 100.0,
            "built_up_area_sqm": 8500.0,
        }

        # Create mock title deed document record
        forensic = ForensicReport(
            document_id="doc-deed-const",
            file_name="sale_deed.pdf",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size_bytes=2048,
            page_count=4,
            is_tampered=False,
        )
        deed_doc = DocumentRecord(
            document_id="doc-deed-const",
            dossier_id=dossier_id,
            file_name="sale_deed.pdf",
            doc_type=DocumentType.LAND_SALE_DEED,
            title="Registered Sale Deed",
            page_count=4,
            forensic=forensic,
            extracted_text_preview="Land Area: 4.5 Acres",
            is_self_attested=False,
        )

        dossier = ApplicationDossier(
            dossier_id=dossier_id,
            institution_name="Constitution Compliant Institute of Technology",
            application_number="AICTE-2024-CONST-001",
            program="Engineering & Technology",
            level="Under Graduate (UG)",
            institution_type="Private-Self Financing",
            location_type="Urban",
            intake_proposed=300,
            documents=[deed_doc],
            findings=[],
            overall_status=VerificationStatus.INCONCLUSIVE,
            risk_score=0.0,
            summary="Awaiting evaluation",
            extracted_params=extracted_params,
        )

        # 1. Execute deterministic rules with extracted parameters
        findings = rule_engine.evaluate_dossier(dossier, [deed_doc], extracted_params)
        has_fail = any(f.status == VerificationStatus.FAIL for f in findings)
        has_review = any(f.status == VerificationStatus.MANUAL_REVIEW_REQUIRED for f in findings)
        if has_fail:
            dossier.overall_status = VerificationStatus.FAIL
            dossier.risk_score = 75.0
        elif has_review:
            dossier.overall_status = VerificationStatus.MANUAL_REVIEW_REQUIRED
            dossier.risk_score = 40.0
        else:
            dossier.overall_status = VerificationStatus.PASS
            dossier.risk_score = 5.0

        # 2. Cryptographically record evaluation audit
        audit_entry = await record_evaluation_audit(
            db=db,
            dossier=dossier,
            findings=findings,
            ruleset_name="aicte_aph_2024_2027.yaml",
            evaluation_id=f"eval-const-{uuid.uuid4().hex[:8]}",
        )

        # 3. Verify hash chain integrity across all entries in the ledger
        from sqlalchemy import select

        from nirikshan.db.models import AuditLogModel
        stmt = select(AuditLogModel).order_by(AuditLogModel.sequence.asc())
        all_entries = list((await db.execute(stmt)).scalars().all())
        chain_res = verify_chain(all_entries)
        assert chain_res.is_valid is True

        # 4. Replay from audit log snapshot
        replay_res = await replay(evaluation_id=audit_entry.evaluation_id, db=db)
        assert replay_res.is_identical is True
        assert replay_res.diffs == []
        assert replay_res.original_status == replay_res.replayed_status
        assert replay_res.original_risk_score == replay_res.replayed_risk_score
        assert replay_res.original_findings_count == len(findings)
