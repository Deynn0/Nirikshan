"""Generates realistic AICTE scrutiny dossiers with valid PDFs and seeds the database."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from nirikshan.config import settings
from nirikshan.db.models import DocumentModel, DossierModel, FindingModel
from nirikshan.db.session import SyncSessionLocal, init_db_sync
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.parsers.pdf_parser import pdf_analyzer
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType


def create_pdf(
    file_path: Path,
    title: str,
    institution: str,
    app_no: str,
    body_paragraphs: list[str],
    table_data: list[list[str]] | None = None,
    tamper_with_bytes: bool = False,
) -> None:
    """Create a structured regulatory PDF."""
    doc = SimpleDocTemplate(str(file_path), pagesize=letter)
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "GovtHeader",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12,
    )
    sub_style = ParagraphStyle(
        "SubHeader",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15,
    )
    body_style = ParagraphStyle(
        "LegalBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10,
    )

    story = [
        Paragraph(title.upper(), header_style),
        Paragraph(f"Reference Institution: {institution} | Application: {app_no}", sub_style),
        Spacer(1, 10),
    ]

    for p in body_paragraphs:
        story.append(Paragraph(p, body_style))

    if table_data:
        t = Table(table_data, colWidths=[150, 300])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(Spacer(1, 10))
        story.append(t)

    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "<b>ISSUING AUTHORITY ENDORSEMENT</b><br/>"
            "This document is cryptographically verified and registered under the state e-District portal.<br/>"
            "Digital Signature ID: DS-AICTE-REG-2024-X901",
            sub_style,
        )
    )

    doc.build(story)

    if tamper_with_bytes:
        # Inject structural tamper: multiple incremental updates and JS indicator
        raw = file_path.read_bytes()
        tampered_raw = raw + b"\n%%EOF\n%%EOF\n%%EOF\n%%EOF\n%%EOF\n/JavaScript (alert('tamper'))\n"
        file_path.write_bytes(tampered_raw)


def seed_database() -> None:
    """Generate sample dossiers and seed SQLite database."""
    init_db_sync()
    session = SyncSessionLocal()

    # Clear existing data for fresh seed
    session.query(FindingModel).delete()
    session.query(DocumentModel).delete()
    session.query(DossierModel).delete()
    session.commit()

    quarantine = settings.quarantine_dir
    quarantine.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # 1. DOSSIER 1: Apex Institute of Technology (Fully Compliant)
    # -------------------------------------------------------------
    dos1_id = "dos-apex-001"
    dos1 = DossierModel(
        dossier_id=dos1_id,
        institution_name="Apex Institute of Technology & Science",
        application_number="AICTE/2024/APEX/108",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
        overall_status="INCONCLUSIVE",
        risk_score=5.0,
        summary="Compliant: All AICTE statutory criteria verified by deterministic rules.",
    )
    dos1_params = {
        "land_area_acres": 3.75,
        "is_contiguous": True,
        "survey_no_deed": "248/1A",
        "survey_no_conversion": "248/1A",
        "survey_no_building_plan": "248/1A",
        "built_up_area_sqm": 14200.0,
        "plan_sanction_no": "DTCP/BLD/2023/1108",
        "conversion_order_no": "REV/CONV/2023/889",
        "conversion_order_date": "2023-11-15",
        "fire_noc_expired": False,
        "faculty_count": 82,
        "cadre_professors": 10,
        "cadre_assoc_professors": 22,
        "cadre_asst_professors": 50,
        "fdr_amount_lakhs": 100.0,
        "fdr_joint_aicte": True,
    }
    dos1.set_extracted_params(dos1_params)
    session.add(dos1)

    # Documents for Dossier 1
    d1_deed_path = quarantine / f"{dos1_id}_land_sale_deed.pdf"
    create_pdf(
        d1_deed_path,
        "Registered Freehold Sale Deed (Sub-Registrar Book-1)",
        dos1.institution_name,
        dos1.application_number,
        [
            "This registered indenture confirms outright ownership of 3.75 Acres of contiguous land situated in Survey No. 248/1A.",
            "The vendor confirms clear, unencumbered title free from mortgage, lis pendens, or third-party alienation.",
        ],
        [
            ["Survey Number", "248/1A"],
            ["Extent of Land", "3.75 Acres"],
            ["Classification", "Urban Institutional"],
        ],
    )

    d1_conv_path = quarantine / f"{dos1_id}_land_conversion_order.pdf"
    create_pdf(
        d1_conv_path,
        "Land Use Conversion Order (Competent Revenue Authority)",
        dos1.institution_name,
        dos1.application_number,
        [
            "Sanction is hereby accorded for conversion of land in Survey No. 248/1A to Educational & Institutional use under Section 95 of Land Revenue Act.",
        ],
        [
            ["Order Number", "REV/CONV/2023/889"],
            ["Survey Number", "248/1A"],
            ["Permitted Use", "Educational / AICTE Technical College"],
        ],
    )

    d1_bld_path = quarantine / f"{dos1_id}_approved_building_plan.pdf"
    create_pdf(
        d1_bld_path,
        "Approved Building Sanction Drawing & Master Plan",
        dos1.institution_name,
        dos1.application_number,
        [
            "Sanctioned drawing approval granted by Directorate of Town and Country Planning for 14,200 sq.m built-up area in Survey No. 248/1A.",
        ],
        [
            ["Approval Ref", "DTCP/BLD/2023/1108"],
            ["Built-up Area", "14,200 sq.m"],
            ["Survey Number", "248/1A"],
        ],
    )

    d1_fire_path = quarantine / f"{dos1_id}_fire_safety_noc.pdf"
    create_pdf(
        d1_fire_path,
        "Fire and Life Safety Certificate (State Fire Service)",
        dos1.institution_name,
        dos1.application_number,
        [
            "Certified that fire fighting installations, hose reels, yard hydrants, and egress stairs comply with National Building Code Part IV. Valid through 2026.",
        ],
        [
            ["NOC Number", "FS/NOC/2024/902"],
            ["Validity Status", "Current & Valid"],
            ["NBC Compliance", "Compliant"],
        ],
    )

    d1_fac_path = quarantine / f"{dos1_id}_faculty_master_list.pdf"
    create_pdf(
        d1_fac_path,
        "Verified Faculty Roster & Cadre Distribution",
        dos1.institution_name,
        dos1.application_number,
        [
            "Master roster of full-time regular faculty appointed through University Selection Committee. 82 regular faculty members verified.",
        ],
        [
            ["Total Faculty", "82 Members"],
            ["Professors", "10"],
            ["Associate Professors", "22"],
            ["Assistant Professors", "50"],
        ],
    )

    d1_fdr_path = quarantine / f"{dos1_id}_fdr_security_deposit.pdf"
    create_pdf(
        d1_fdr_path,
        "Fixed Deposit Receipt (Joint Account with AICTE)",
        dos1.institution_name,
        dos1.application_number,
        [
            "Joint Fixed Deposit Receipt held with State Bank of India in joint names of Regional Officer, AICTE and Chairman of Apex Educational Trust.",
        ],
        [
            ["FDR Amount", "INR 100 Lakhs"],
            ["Joint Holder", "Regional Officer AICTE"],
            ["Maturity Period", "10 Years"],
        ],
    )

    doc_files_d1 = [
        (d1_deed_path, DocumentType.LAND_SALE_DEED, "Registered Sale Deed (Freehold Land)"),
        (
            d1_conv_path,
            DocumentType.LAND_USE_CONVERSION_CERT,
            "Revenue Land Conversion Certificate",
        ),
        (d1_bld_path, DocumentType.BUILDING_PLAN_APPROVED, "DTCP Sanctioned Building Plan"),
        (d1_fire_path, DocumentType.FIRE_SAFETY_NOC, "State Fire Safety NOC"),
        (d1_fac_path, DocumentType.FACULTY_MASTER_LIST, "Faculty Appointment Roster"),
        (d1_fdr_path, DocumentType.FDR_RECEIPT, "Joint AICTE Security Deposit FDR"),
    ]

    for f_path, doc_type, title in doc_files_d1:
        f_report, preview, _ = pdf_analyzer.analyze_file(f_path, f_path.stem)
        d_model = DocumentModel(
            document_id=f"doc-{f_path.stem}",
            dossier_id=dos1_id,
            file_name=f_path.name,
            doc_type=doc_type.value,
            title=title,
            quarantine_path=str(f_path),
            page_count=f_report.page_count,
            sha256_hash=f_report.sha256_hash,
            is_self_attested=False,
            is_tampered=False,
            forensic_json=f_report.model_dump_json(),
            text_preview=preview,
        )
        session.add(d_model)

    # -------------------------------------------------------------
    # 2. DOSSIER 2: Shivalik Engineering Academy (Shortfall Land & Expired Fire NOC)
    # -------------------------------------------------------------
    dos2_id = "dos-shivalik-002"
    dos2 = DossierModel(
        dossier_id=dos2_id,
        institution_name="Shivalik Institute of Engineering & Management",
        application_number="AICTE/2024/SHIV/045",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
        overall_status="INCONCLUSIVE",
        risk_score=75.0,
        summary="Deficiencies identified against AICTE APH 2024-2027 statutory requirements.",
    )
    dos2_params = {
        "land_area_acres": 1.8,  # Deficient: Requires 2.5 Acres in Urban
        "is_contiguous": True,
        "survey_no_deed": "44/B",
        "survey_no_conversion": "44/B",
        "lease_years": 15,  # Deficient: Requires 30 years
        "is_government_lease": False,
        "fire_noc_expired": True,  # Deficient
        "faculty_count": 55,  # Shortfall: Requires 80 for 1200 students
        "cadre_professors": 1,
        "cadre_assoc_professors": 4,
        "cadre_asst_professors": 50,
        "fdr_amount_lakhs": 35.0,  # Below statutory
        "fdr_joint_aicte": False,
    }
    dos2.set_extracted_params(dos2_params)
    session.add(dos2)

    d2_lease_path = quarantine / f"{dos2_id}_lease_deed.pdf"
    create_pdf(
        d2_lease_path,
        "Private Land Lease Deed",
        dos2.institution_name,
        dos2.application_number,
        [
            "Lease agreement executed with private landlord for 1.8 Acres of land for a term of 15 years.",
        ],
        [["Survey Number", "44/B"], ["Area", "1.8 Acres"], ["Lease Term", "15 Years (Private)"]],
    )

    d2_fire_path = quarantine / f"{dos2_id}_expired_fire_noc.pdf"
    create_pdf(
        d2_fire_path,
        "Expired Fire Safety Clearance",
        dos2.institution_name,
        dos2.application_number,
        [
            "Temporary fire clearance issued in 2021. Expired on 31st March 2023. Renewal pending inspection.",
        ],
        [["NOC Number", "FS/NOC/2021/112"], ["Validity Status", "EXPIRED 31-03-2023"]],
    )

    doc_files_d2 = [
        (d2_lease_path, DocumentType.LAND_LEASE_DEED, "Private Lease Deed (15 Years)"),
        (d2_fire_path, DocumentType.FIRE_SAFETY_NOC, "Expired Fire Clearance Certificate"),
    ]

    for f_path, doc_type, title in doc_files_d2:
        f_report, preview, _ = pdf_analyzer.analyze_file(f_path, f_path.stem)
        d_model = DocumentModel(
            document_id=f"doc-{f_path.stem}",
            dossier_id=dos2_id,
            file_name=f_path.name,
            doc_type=doc_type.value,
            title=title,
            quarantine_path=str(f_path),
            page_count=f_report.page_count,
            sha256_hash=f_report.sha256_hash,
            is_self_attested=False,
            is_tampered=False,
            forensic_json=f_report.model_dump_json(),
            text_preview=preview,
        )
        session.add(d_model)

    # -------------------------------------------------------------
    # 3. DOSSIER 3: Modern Technical College (Tampered PDF & Survey Mismatch)
    # -------------------------------------------------------------
    dos3_id = "dos-modern-003"
    dos3 = DossierModel(
        dossier_id=dos3_id,
        institution_name="Modern College of Engineering & Research",
        application_number="AICTE/2024/MOD/771",
        program="Engineering & Technology",
        level="Under Graduate (UG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=300,
        overall_status="INCONCLUSIVE",
        risk_score=95.0,
        summary="ALERT: Document tamper or structural anomaly detected. Committee investigation recommended.",
    )
    dos3_params = {
        "land_area_acres": 4.5,
        "survey_no_deed": "112/A",
        "survey_no_conversion": "904/X",  # DISCREPANCY! Mismatched Survey Number!
        "survey_no_building_plan": "112/A",
    }
    dos3.set_extracted_params(dos3_params)
    session.add(dos3)

    d3_tampered_deed = quarantine / f"{dos3_id}_tampered_sale_deed.pdf"
    create_pdf(
        d3_tampered_deed,
        "Sub-Registrar Deed (Altered PDF Stream)",
        dos3.institution_name,
        dos3.application_number,
        [
            "Sale Deed for Survey No. 112/A purporting to transfer 4.5 Acres of land.",
        ],
        [["Survey Number", "112/A"], ["Extent", "4.5 Acres"]],
        tamper_with_bytes=True,  # Injected high incremental updates and JS!
    )

    d3_conv_order = quarantine / f"{dos3_id}_conversion_order_mismatch.pdf"
    create_pdf(
        d3_conv_order,
        "Revenue Conversion Order",
        dos3.institution_name,
        dos3.application_number,
        [
            "Conversion order issued exclusively for Survey No. 904/X situated in adjacent taluk.",
        ],
        [["Survey Number", "904/X"], ["Alienation Status", "Different Parcel"]],
    )

    doc_files_d3 = [
        (d3_tampered_deed, DocumentType.LAND_SALE_DEED, "Tampered Land Sale Deed"),
        (d3_conv_order, DocumentType.LAND_USE_CONVERSION_CERT, "Mismatched Conversion Order"),
    ]

    for f_path, doc_type, title in doc_files_d3:
        f_report, preview, _ = pdf_analyzer.analyze_file(f_path, f_path.stem)
        d_model = DocumentModel(
            document_id=f"doc-{f_path.stem}",
            dossier_id=dos3_id,
            file_name=f_path.name,
            doc_type=doc_type.value,
            title=title,
            quarantine_path=str(f_path),
            page_count=f_report.page_count,
            sha256_hash=f_report.sha256_hash,
            is_self_attested=False,
            is_tampered=f_report.is_tampered,
            forensic_json=f_report.model_dump_json(),
            text_preview=preview,
        )
        session.add(d_model)

    # -------------------------------------------------------------
    # 4. DOSSIER 4: Global Management Institute (Self-Attestation & Advisory Only)
    # -------------------------------------------------------------
    dos4_id = "dos-global-004"
    dos4 = DossierModel(
        dossier_id=dos4_id,
        institution_name="Global Institute of Management & Technology",
        application_number="AICTE/2024/GLO/230",
        program="Management",
        level="Post Graduate (PG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=180,
        overall_status="INCONCLUSIVE",
        risk_score=40.0,
        summary="Self-attestations or model outputs require manual committee scrutiny.",
    )
    dos4_params = {
        "land_area_acres": 2.5,
        "faculty_count": 24,
        "faculty_count_from_model": True,  # Model Advisory Only!
    }
    dos4.set_extracted_params(dos4_params)
    session.add(dos4)

    d4_affidavit = quarantine / f"{dos4_id}_self_declaration_affidavit.pdf"
    create_pdf(
        d4_affidavit,
        "Notarized Self-Attested Declaration on Non-Judicial Stamp",
        dos4.institution_name,
        dos4.application_number,
        [
            "I, Chairman of Global Educational Trust, hereby solemnly declare that the institution maintains barrier free ramps and adequate cadre faculty.",
            "NON-NEGOTIABLE PRINCIPLE 1: This self-attestation NEVER counts as verified evidence for regulatory scrutiny.",
        ],
        [["Declaration Type", "Self-Attested Affidavit"], ["Regulatory Value", "UNVERIFIED CLAIM"]],
    )

    doc_files_d4 = [
        (
            d4_affidavit,
            DocumentType.AFFIDAVIT_SELF_DECLARATION,
            "Applicant Self-Declaration Affidavit",
        ),
    ]

    for f_path, doc_type, title in doc_files_d4:
        f_report, preview, _ = pdf_analyzer.analyze_file(f_path, f_path.stem)
        d_model = DocumentModel(
            document_id=f"doc-{f_path.stem}",
            dossier_id=dos4_id,
            file_name=f_path.name,
            doc_type=doc_type.value,
            title=title,
            quarantine_path=str(f_path),
            page_count=f_report.page_count,
            sha256_hash=f_report.sha256_hash,
            is_self_attested=True,
            is_tampered=False,
            forensic_json=f_report.model_dump_json(),
            text_preview=preview,
        )
        session.add(d_model)

    session.commit()

    # Now execute verification for all dossiers so their findings are fully pre-populated!
    for dossier_record in [dos1, dos2, dos3, dos4]:
        # Convert to schema
        docs_schema: list[DocumentRecord] = []
        for doc in dossier_record.documents:
            forensic_obj = pdf_analyzer.analyze_file(Path(doc.quarantine_path), doc.document_id)[0]
            docs_schema.append(
                DocumentRecord(
                    document_id=doc.document_id,
                    dossier_id=dossier_record.dossier_id,
                    file_name=doc.file_name,
                    doc_type=DocumentType(doc.doc_type),
                    title=doc.title,
                    page_count=doc.page_count,
                    forensic=forensic_obj,
                    extracted_text_preview=doc.text_preview,
                    is_self_attested=doc.is_self_attested,
                )
            )

        dossier_schema = ApplicationDossier(
            dossier_id=dossier_record.dossier_id,
            institution_name=dossier_record.institution_name,
            application_number=dossier_record.application_number,
            program=dossier_record.program,
            level=dossier_record.level,
            institution_type=dossier_record.institution_type,
            location_type=dossier_record.location_type,
            intake_proposed=dossier_record.intake_proposed,
            created_at=dossier_record.created_at,
            documents=docs_schema,
        )

        findings = rule_engine.evaluate_dossier(
            dossier_schema, docs_schema, dossier_record.get_extracted_params()
        )

        # Update status
        has_tamper = any(f.status == VerificationStatus.FLAGGED_TAMPER for f in findings)
        has_fail = any(f.status == VerificationStatus.FAIL for f in findings)
        has_review = any(f.status == VerificationStatus.MANUAL_REVIEW_REQUIRED for f in findings)

        if has_tamper:
            dossier_record.overall_status = VerificationStatus.FLAGGED_TAMPER.value
            dossier_record.risk_score = 95.0
            dossier_record.summary = "ALERT: Document tamper or structural anomaly detected. Committee investigation recommended."
        elif has_fail:
            dossier_record.overall_status = VerificationStatus.FAIL.value
            dossier_record.risk_score = 75.0
            dossier_record.summary = (
                "Deficiencies identified against AICTE APH 2024-2027 statutory requirements."
            )
        elif has_review:
            dossier_record.overall_status = VerificationStatus.MANUAL_REVIEW_REQUIRED.value
            dossier_record.risk_score = 40.0
            dossier_record.summary = (
                "Self-attestations or model outputs require manual committee scrutiny."
            )
        else:
            dossier_record.overall_status = VerificationStatus.PASS.value
            dossier_record.risk_score = 5.0
            dossier_record.summary = (
                "Compliant: All AICTE statutory criteria verified by deterministic rules."
            )

        import json

        for f in findings:
            f_model = FindingModel(
                finding_id=f.finding_id,
                dossier_id=dossier_record.dossier_id,
                rule_id=f.rule_id,
                rule_name=f.rule_name,
                category=f.category,
                status=f.status.value,
                summary=f.summary,
                details=f.details,
                handbook_citation_json=f.handbook_citation.model_dump_json(),
                evidence_list_json=json.dumps([e.model_dump(mode="json") for e in f.evidence_list]),
                bounding_box_json=f.primary_bounding_box.model_dump_json()
                if f.primary_bounding_box
                else "{}",
                advisory_notes_json=json.dumps(f.advisory_notes),
                is_model_advisory_only=f.is_model_advisory_only,
                needs_verification=f.needs_verification,
            )
            session.add(f_model)

    session.commit()
    session.close()
    print(
        "Database successfully seeded with 4 representative AICTE dossiers and verified findings."
    )


if __name__ == "__main__":
    seed_database()
