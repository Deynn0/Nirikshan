"""
Nirikshan Project — Comprehensive PDF Analysis Report Generator
Uses ReportLab Platypus framework for professional multi-page output.
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.colors import HexColor, white, black

# ── Colour Palette ──────────────────────────────────────────────────────────
C_NAVY      = HexColor("#1E293B")   # dark headers
C_INDIGO    = HexColor("#6366F1")   # accent
C_INDIGO_LT = HexColor("#EEF2FF")   # light accent bg
C_EMERALD   = HexColor("#10B981")   # PASS / good
C_EMERALD_LT= HexColor("#D1FAE5")
C_ROSE      = HexColor("#EF4444")   # FAIL / CRITICAL
C_ROSE_LT   = HexColor("#FEE2E2")
C_AMBER     = HexColor("#F59E0B")   # warnings / HIGH
C_AMBER_LT  = HexColor("#FEF3C7")
C_SLATE     = HexColor("#475569")   # body text
C_SLATE_LT  = HexColor("#F1F5F9")   # alternating row
C_SLATE_MID = HexColor("#CBD5E1")   # border
C_WHITE     = white

OUTPUT_PATH = r"C:\Users\Admin\.gemini\antigravity\brain\fc457a60-34cf-444d-a6b2-53ff4e65ed48\nirikshan_analysis_report.pdf"

# ── Styles ───────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    styles = {
        "cover_title": S("cover_title",
            fontName="Helvetica-Bold", fontSize=36, textColor=C_WHITE,
            leading=44, alignment=TA_CENTER, spaceAfter=8),
        "cover_subtitle": S("cover_subtitle",
            fontName="Helvetica", fontSize=16, textColor=HexColor("#94A3B8"),
            leading=22, alignment=TA_CENTER, spaceAfter=4),
        "cover_tagline": S("cover_tagline",
            fontName="Helvetica-Oblique", fontSize=13, textColor=HexColor("#A5B4FC"),
            leading=18, alignment=TA_CENTER, spaceAfter=20),
        "cover_stat": S("cover_stat",
            fontName="Helvetica-Bold", fontSize=11, textColor=C_EMERALD,
            leading=16, alignment=TA_CENTER),

        "h1": S("h1",
            fontName="Helvetica-Bold", fontSize=18, textColor=C_NAVY,
            leading=24, spaceBefore=18, spaceAfter=6,
            borderPad=4),
        "h2": S("h2",
            fontName="Helvetica-Bold", fontSize=13, textColor=C_INDIGO,
            leading=18, spaceBefore=14, spaceAfter=4),
        "h3": S("h3",
            fontName="Helvetica-Bold", fontSize=11, textColor=C_NAVY,
            leading=15, spaceBefore=10, spaceAfter=3),
        "body": S("body",
            fontName="Helvetica", fontSize=9.5, textColor=C_SLATE,
            leading=14, spaceAfter=4, alignment=TA_JUSTIFY),
        "body_bullet": S("body_bullet",
            fontName="Helvetica", fontSize=9.5, textColor=C_SLATE,
            leading=14, leftIndent=14, spaceAfter=2,
            bulletIndent=4),
        "code": S("code",
            fontName="Courier", fontSize=8, textColor=HexColor("#1E40AF"),
            leading=11, backColor=HexColor("#F8FAFC"),
            leftIndent=8, rightIndent=8, spaceAfter=2),
        "th": S("th",
            fontName="Helvetica-Bold", fontSize=8.5, textColor=C_WHITE,
            leading=12, alignment=TA_CENTER),
        "td": S("td",
            fontName="Helvetica", fontSize=8.5, textColor=C_SLATE,
            leading=12, alignment=TA_LEFT),
        "td_center": S("td_center",
            fontName="Helvetica", fontSize=8.5, textColor=C_SLATE,
            leading=12, alignment=TA_CENTER),
        "td_bold": S("td_bold",
            fontName="Helvetica-Bold", fontSize=8.5, textColor=C_NAVY,
            leading=12, alignment=TA_LEFT),
        "caption": S("caption",
            fontName="Helvetica-Oblique", fontSize=8, textColor=HexColor("#94A3B8"),
            leading=11, alignment=TA_CENTER, spaceAfter=6),
        "section_intro": S("section_intro",
            fontName="Helvetica", fontSize=10, textColor=HexColor("#334155"),
            leading=15, spaceAfter=6, alignment=TA_JUSTIFY,
            leftIndent=0),
        "stat_label": S("stat_label",
            fontName="Helvetica-Bold", fontSize=9, textColor=C_NAVY,
            leading=13),
    }
    return styles


# ── Helper: table style builder ───────────────────────────────────────────────
def base_table_style(header_bg=None):
    hbg = header_bg or C_NAVY
    return TableStyle([
        # Header row
        ("BACKGROUND",  (0,0), (-1,0), hbg),
        ("TEXTCOLOR",   (0,0), (-1,0), C_WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,0), 8.5),
        ("ALIGN",       (0,0), (-1,0), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING",(0,0), (-1,-1), 6),
        # Grid
        ("GRID",        (0,0), (-1,-1), 0.4, C_SLATE_MID),
        ("LINEABOVE",   (0,0), (-1,0), 1.5, hbg),
        ("LINEBELOW",   (0,-1), (-1,-1), 1, C_SLATE_MID),
        # Alt rows
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WHITE, C_SLATE_LT]),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,1), (-1,-1), 8.5),
        ("ALIGN",       (0,1), (-1,-1), "LEFT"),
    ])


def alt_row(ts, col, row, color):
    ts.add("BACKGROUND", (col, row), (col, row), color)


# ── Page template callbacks ───────────────────────────────────────────────────
def _make_page_callbacks(doc):
    def on_first_page(canvas, doc):
        # Cover page — no header/footer numbers
        pass

    def on_later_pages(canvas, doc):
        canvas.saveState()
        # Footer bar
        canvas.setFillColor(C_NAVY)
        canvas.rect(0, 0, A4[0], 22*mm, fill=1, stroke=0)

        canvas.setFont("Helvetica-Bold", 7)
        canvas.setFillColor(C_WHITE)
        canvas.drawString(1.5*cm, 8*mm, "NIRIKSHAN  |  AICTE Regulatory Scrutiny Platform  |  CONFIDENTIAL")

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#94A3B8"))
        pn = "Page %d" % doc.page
        canvas.drawRightString(A4[0] - 1.5*cm, 8*mm, pn)

        # Top hairline
        canvas.setStrokeColor(C_INDIGO)
        canvas.setLineWidth(2)
        canvas.line(0, A4[1] - 10*mm, A4[0], A4[1] - 10*mm)
        canvas.restoreState()

    return on_first_page, on_later_pages


# ── Cover Page ────────────────────────────────────────────────────────────────
def cover_page(S):
    story = []

    # Background navy block simulated via table spanning full width
    cover_data = [[""]]
    cover_tbl = Table(cover_data, colWidths=[17*cm], rowHeights=[4*cm])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_NAVY),
        ("GRID", (0,0), (-1,-1), 0, C_NAVY),
    ]))

    story.append(Spacer(1, 2.5*cm))

    # Title block
    story.append(Paragraph("NIRIKSHAN", S["cover_title"]))
    story.append(Paragraph("निरीक्षण", ParagraphStyle("deva",
        fontName="Helvetica-Bold", fontSize=22, textColor=HexColor("#A5B4FC"),
        leading=28, alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph(
        "Offline-First, Explainable Regulatory Scrutiny Platform",
        S["cover_subtitle"]))
    story.append(Paragraph(
        "AICTE Approval Process Handbook (APH) — Institutional Evaluation System",
        S["cover_tagline"]))

    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="80%", thickness=1, color=C_INDIGO,
                             spaceAfter=0.6*cm, spaceBefore=0, hAlign="CENTER"))

    # Key stats strip
    stats = [
        ["Python 3.11 / FastAPI", "React 19 / TypeScript 5", "Air-Gapped Runtime"],
        ["10 API Route Modules",  "7+ Backend Subsystems",   "14 AICTE APH Rules"],
        ["100% Precision / Recall","0% False Alarm Rate",    "24 Synthetic Applications"],
    ]
    stat_tbl = Table(stats, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    stat_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), HexColor("#0F172A")),
        ("TEXTCOLOR",    (0,0), (-1,-1), C_EMERALD),
        ("FONTNAME",     (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 9.5),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0), (-1,-1), 7),
        ("GRID",         (0,0), (-1,-1), 0.5, HexColor("#1E293B")),
        ("ROUNDEDCORNERS", (0,0), (-1,-1), 4),
    ]))
    story.append(stat_tbl)

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="80%", thickness=1, color=C_INDIGO,
                             spaceAfter=0.5*cm, spaceBefore=0, hAlign="CENTER"))

    story.append(Paragraph(
        "Comprehensive Project Analysis Report  —  November 2026",
        ParagraphStyle("cover_date",
            fontName="Helvetica", fontSize=10,
            textColor=HexColor("#94A3B8"),
            alignment=TA_CENTER, leading=14)))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "CONFIDENTIAL  |  FOR INTERNAL USE ONLY",
        ParagraphStyle("cover_conf",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=C_ROSE,
            alignment=TA_CENTER, leading=12)))

    story.append(PageBreak())
    return story


# ── Section helpers ───────────────────────────────────────────────────────────
def section_heading(text, S, level=1):
    tag = f"h{level}"
    items = []
    if level == 1:
        items.append(HRFlowable(width="100%", thickness=2, color=C_INDIGO,
                                 spaceAfter=4, spaceBefore=12))
    items.append(Paragraph(text, S[tag]))
    if level == 1:
        items.append(HRFlowable(width="100%", thickness=0.5, color=C_SLATE_MID,
                                 spaceAfter=6, spaceBefore=0))
    return items


def bullets(items_list, S, prefix="•"):
    return [Paragraph(f"{prefix}  {t}", S["body_bullet"]) for t in items_list]


# ════════════════════════════════════════════════════════════════════════════
# BUILD STORY
# ════════════════════════════════════════════════════════════════════════════
def build_story(S):
    story = []

    # ── SECTION 1 — Executive Summary ────────────────────────────────────────
    story += section_heading("Section 1 — Executive Summary", S, 1)
    story.append(Paragraph(
        "Nirikshan is a full-stack, air-gapped document scrutiny platform designed to assist AICTE scrutiny "
        "officers in evaluating institutional approval applications. The system enforces a strict evidential "
        "trust hierarchy, ensures 100% offline operation, and produces fully explainable, citation-backed "
        "findings for every regulatory rule evaluated.", S["section_intro"]))

    story.append(Spacer(1, 0.3*cm))
    kv = [
        ["Stack",         "Python 3.11 / FastAPI backend  +  React 19 / TypeScript 5 frontend"],
        ["Scale",         "10 API route modules, 7+ backend subsystems"],
        ["Benchmark",     "100% Precision / Recall across 10 fraud categories, 24 synthetic applications"],
        ["False Alarms",  "0% false alarm rate on clean controls (dev + blind held-out splits)"],
        ["Connectivity",  "Air-gapped — zero outbound network connections at runtime"],
    ]
    kv_tbl = Table(kv, colWidths=[3.8*cm, 13*cm])
    kv_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (0,-1), C_NAVY),
        ("TEXTCOLOR",    (0,0), (0,-1), C_WHITE),
        ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 7),
        ("GRID",         (0,0), (-1,-1), 0.4, C_SLATE_MID),
        ("ROWBACKGROUNDS",(1,0),(1,-1), [C_WHITE, C_SLATE_LT]),
        ("TEXTCOLOR",    (1,0), (1,-1), C_SLATE),
    ]))
    story.append(kv_tbl)

    story.append(PageBreak())

    # ── SECTION 2 — Constitution ──────────────────────────────────────────────
    story += section_heading("Section 2 — The Nirikshan Constitution (Core Design Principles)", S, 1)
    story.append(Paragraph(
        "Five non-negotiable constitutional invariants govern every component of the platform:", S["section_intro"]))
    story.append(Spacer(1, 0.2*cm))

    principles = [
        ("1. Trust Ladder Hierarchy & Strict PASS Trust-Gating",
         "Evidence ranks: CRYPTOGRAPHIC (60) > ISSUER (50) > RECORD (40) > RULE (30) > "
         "STRUCTURAL_FORENSIC (20) > MODEL (10) > UNVERIFIED_CLAIM (0). "
         "Self-attestation always = UNVERIFIED_CLAIM. ML models are always advisory-only. "
         "No MODEL or self-attested item can ever produce a verified PASS or FAIL.",
         C_INDIGO_LT),
        ("2. Mandatory Sandboxed Ingestion",
         "All untrusted applicant PDFs stored in AES-GCM-256 encrypted quarantine, parsed inside "
         "isolated worker subprocess with RLIMIT_AS, RLIMIT_CPU, and timeout watchdog.",
         C_SLATE_LT),
        ("3. 100% Offline & Air-Gapped Operation",
         "Zero outbound network at runtime. All non-loopback socket connections blocked at socket "
         "layer via _install_airgap_guard().",
         C_INDIGO_LT),
        ("4. Full Explainability & Citations",
         "Every finding includes authoritative handbook citation (Clause, Page, Edition), itemized "
         "evidence with trust levels, and spatial bounding boxes [page, x, y, width, height].",
         C_SLATE_LT),
        ("5. Cryptographic Audit Ledger & Deterministic Replay",
         "Every evaluation step committed to append-only SHA-256 hash-chained ledger. Full historical "
         "replay for deterministic consistency verification.",
         C_INDIGO_LT),
    ]
    for title, desc, bg in principles:
        tbl = Table([[Paragraph(title, S["h3"]),
                      Paragraph(desc, S["body"])]], colWidths=[5*cm, 11.8*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), bg),
            ("GRID",         (0,0), (-1,-1), 0.3, C_SLATE_MID),
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
            ("TOPPADDING",   (0,0), (-1,-1), 7),
            ("BOTTOMPADDING",(0,0), (-1,-1), 7),
            ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.15*cm))

    story.append(PageBreak())

    # ── SECTION 3 — Architecture ──────────────────────────────────────────────
    story += section_heading("Section 3 — System Architecture", S, 1)

    story += section_heading("3.1  Backend Modules (Python 3.11 / FastAPI)", S, 2)
    be_hdr = [["Module", "Path", "Purpose"]]
    be_rows = [
        ["advisory",  "nirikshan/advisory/", "YOLOX-M vision model, Ask-Why LLM, entity extraction, grounding"],
        ["api",       "nirikshan/api/",       "FastAPI route handlers (10 routers)"],
        ["core",      "nirikshan/core/",      "Config, DB session, safe_eval, rule schema"],
        ["engine",    "nirikshan/engine/",    "Audit log, SHA-256 hash-chaining, replay"],
        ["fraud",     "nirikshan/fraud/",     "NetworkX fraud graph, ring detection"],
        ["ingest",    "nirikshan/ingest/",    "PDF text extractor, pikepdf metadata, font analysis, rasterizer"],
        ["rules",     "nirikshan/rules/",     "AST-safe deterministic rules engine, trust-gating"],
        ["sandbox",   "nirikshan/sandbox/",   "Sandboxed subprocess worker, quarantine storage"],
        ["schemas",   "nirikshan/schemas/",   "Pydantic v2 domain models (Finding, Dossier, Evidence)"],
        ["trust",     "nirikshan/trust/",     "Trust ladder hierarchy, evidence decisiveness"],
        ["worker",    "nirikshan/worker/",    "Async job service, runner, sandbox worker"],
        ["parsers",   "nirikshan/parsers/",   "PDF parser"],
        ["rulesets",  "rulesets/",            "Declarative AICTE APH regulatory rules (YAML)"],
    ]
    be_tbl = Table(be_hdr + be_rows, colWidths=[2.5*cm, 4*cm, 10.3*cm])
    ts = base_table_style(C_NAVY)
    be_tbl.setStyle(ts)
    story.append(be_tbl)
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("3.2  API Routes", S, 2)
    routes = [
        ["/api/auth",     "Authentication"],
        ["/api/dossiers", "Dossier CRUD and scrutiny"],
        ["/api/documents","Document upload and management"],
        ["/api/jobs",     "Async job processing"],
        ["/api/audit",    "Audit ledger access"],
        ["/api/rules",    "Ruleset inspection"],
        ["/api/reports",  "Report generation"],
        ["/api/scan",     "Forensic scanning"],
        ["/api/advisory", "ML advisory pipeline"],
        ["/api/fraud",    "Fraud graph analysis"],
    ]
    r_tbl = Table([["Route", "Description"]] + routes, colWidths=[4.5*cm, 12.3*cm])
    r_tbl.setStyle(base_table_style(C_INDIGO))
    story.append(r_tbl)
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("3.3  Frontend (React 19 / TypeScript 5 / Vite)", S, 2)
    fe_rows = [
        ["OfficerPage",               "Main scrutiny console with 7 tabbed views"],
        ["ApplicantPage",             "Applicant submission interface"],
        ["DocumentViewer",            "Side-by-side PDF canvas with finding bounding boxes"],
        ["RevisionTimeMachine",       "Incremental PDF revision history browser"],
        ["IntegrityNetwork",          "Cytoscape.js fraud network visualization"],
        ["GeotagMap",                 "Leaflet.js geofencing and campus boundary check"],
        ["AskWhyPanel",               "Natural language Q&A over findings"],
        ["DeficiencyLetterGenerator", "Auto-draft deficiency letters"],
        ["TrustLadderBadge",          "Color-coded trust level indicators"],
    ]
    fe_tbl = Table([["Component", "Purpose"]] + fe_rows, colWidths=[5*cm, 11.8*cm])
    fe_tbl.setStyle(base_table_style(C_INDIGO))
    story.append(fe_tbl)

    story.append(PageBreak())

    story += section_heading("3.4  System Dependencies", S, 2)
    story.append(Paragraph("<b>Backend (Python):</b>", S["h3"]))
    story.append(Paragraph(
        "fastapi · uvicorn · pydantic v2 · sqlalchemy · pyyaml · pypdf · pillow · "
        "cryptography · pyhanko · shapely · c2pa-python · qrcode · segno · fonttools · "
        "onnxruntime · networkx · imagehash · rapidfuzz · reportlab · aiofiles · aiosqlite",
        S["code"]))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<b>Frontend (Node / React):</b>", S["h3"]))
    story.append(Paragraph(
        "React 19 · TypeScript 5.7 · Vite 8 · TailwindCSS 3 · TanStack Query 5 · "
        "Cytoscape.js 3 · Leaflet 1.9 · Three.js · i18next · lucide-react · jsPDF · Playwright (E2E)",
        S["code"]))

    story.append(PageBreak())

    # ── SECTION 4 — Trust Ladder ──────────────────────────────────────────────
    story += section_heading("Section 4 — Trust Ladder System (Core Innovation)", S, 1)

    story += section_heading("4.1  Trust Level Definitions", S, 2)
    tl_header = [["Level", "Rank", "Description", "Decisive?"]]
    tl_rows = [
        ["CRYPTOGRAPHIC",       "60", "X.509 PKI, signed QR, Ed25519, cryptographic hashes", "YES"],
        ["ISSUER",              "50", "Verified municipal/authority endorsement", "YES"],
        ["RECORD",              "40", "Official sub-registrar deed, RoR, government gazette", "YES"],
        ["RULE",                "30", "Deterministic mathematical/logical evaluation", "YES"],
        ["STRUCTURAL_FORENSIC", "20", "PDF metadata, font tampering, ELA analysis", "NO"],
        ["MODEL",               "10", "Local OCR/Vision/Heuristics — ADVISORY ONLY", "NO"],
        ["UNVERIFIED_CLAIM",    "0",  "Applicant self-attestation / affidavits", "NO"],
    ]
    tl_colours = [
        HexColor("#064E3B"),  # CRYPTOGRAPHIC — deep green
        HexColor("#065F46"),  # ISSUER
        HexColor("#1E3A5F"),  # RECORD
        HexColor("#312E81"),  # RULE
        HexColor("#78350F"),  # STRUCTURAL_FORENSIC
        HexColor("#7C2D12"),  # MODEL
        HexColor("#4C1D2F"),  # UNVERIFIED_CLAIM
    ]
    tl_tbl_data = tl_header + tl_rows
    tl_tbl = Table(tl_tbl_data, colWidths=[3.8*cm, 1.4*cm, 9.5*cm, 2*cm])
    tl_ts = TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), C_NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8.5),
        ("ALIGN",        (0,0), (-1,0), "CENTER"),
        ("ALIGN",        (1,1), (1,-1), "CENTER"),
        ("ALIGN",        (3,1), (3,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("GRID",         (0,0), (-1,-1), 0.4, HexColor("#334155")),
    ])
    # colour each data row
    for i, (clr, row_data) in enumerate(zip(tl_colours, tl_rows), start=1):
        tl_ts.add("BACKGROUND", (0,i), (-1,i), clr)
        tl_ts.add("TEXTCOLOR",  (0,i), (-1,i), C_WHITE)
        tl_ts.add("FONTNAME",   (0,i), (0,i),  "Helvetica-Bold")
        decisive = row_data[3]
        dcol = C_EMERALD if decisive == "YES" else C_ROSE
        tl_ts.add("TEXTCOLOR",  (3,i), (3,i), dcol)
        tl_ts.add("FONTNAME",   (3,i), (3,i), "Helvetica-Bold")
    tl_tbl.setStyle(tl_ts)
    story.append(tl_tbl)
    story.append(Spacer(1, 0.4*cm))

    story += section_heading("4.2  Trust Gating Logic", S, 2)
    gating_steps = [
        "Merge rule parameters into facts namespace",
        "Run _check_trust_gate() — verify each required evidence type meets min_trust_level",
        "Evaluate logic expression via safe_evaluator (AST-based, no exec/eval)",
        "If logic=True BUT gate fails → emit UNVERIFIED (never PASS)",
        "If logic=True AND gate passes AND all evidence is decisive → emit PASS",
        "If logic=False → emit FAIL",
        "If only MODEL/UNVERIFIED_CLAIM evidence → downgrade to MANUAL_REVIEW_REQUIRED",
    ]
    for idx, step in enumerate(gating_steps, 1):
        story.append(Paragraph(f"<b>Step {idx}.</b>  {step}", S["body_bullet"]))
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("4.3  Evidence Decisiveness Rules", S, 2)
    story.append(Paragraph(
        "An EvidenceItem is decisive (is_decisive=True) only if its effective trust level is NOT in "
        "{MODEL, UNVERIFIED_CLAIM, STRUCTURAL_FORENSIC}.", S["body"]))
    story.append(Paragraph(
        "Special overrides in effective_trust_level():", S["body"]))
    story += bullets([
        "If is_self_attested=True → force UNVERIFIED_CLAIM regardless of declared level",
        "If is_tampered=True → cap at STRUCTURAL_FORENSIC",
    ], S)

    story.append(PageBreak())

    # ── SECTION 5 — Rules Engine ──────────────────────────────────────────────
    story += section_heading("Section 5 — Regulatory Rules Engine (AICTE APH)", S, 1)

    story += section_heading("5.1  Rule Schema Structure (YAML)", S, 2)
    schema_fields = [
        ["Field",                "Description"],
        ["rule_id",              "Unique rule identifier (e.g. AICTE-SAFE-FIRE-001)"],
        ["title",                "Human-readable rule title"],
        ["category",             "Thematic grouping (Safety, Land, Infrastructure, Faculty …)"],
        ["severity",             "CRITICAL / HIGH / MEDIUM / LOW"],
        ["citation",             "document, clause, page, edition, needs_verification flag"],
        ["applicable_years",     "List of academic year strings"],
        ["evidence_requirements","type + min_trust_level per requirement"],
        ["parameters",           "Static values merged into evaluation facts namespace"],
        ["logic",                "AST-safe expression string evaluated by safe_evaluator"],
        ["deficiency_template",  "Jinja-style {key} placeholders rendered on FAIL"],
        ["description",          "Full prose description of the rule"],
    ]
    sf_tbl = Table(schema_fields, colWidths=[4.5*cm, 12.3*cm])
    sf_tbl.setStyle(base_table_style(C_NAVY))
    story.append(sf_tbl)
    story.append(Spacer(1, 0.4*cm))

    story += section_heading("5.2  Sample Rules (AICTE APH 2024–2027)", S, 2)
    rules_hdr = [["Rule ID", "Title", "Category", "Sev.", "Min Trust"]]
    rules_data = [
        ["AICTE-SAFE-FIRE-001", "Fire Safety NOC Validity",             "Safety & Compliance",  "CRIT", "ISSUER"],
        ["AICTE-LAND-OWN-001",  "Land Ownership — Registered Sale Deed","Land & Title",         "CRIT", "RECORD"],
        ["AICTE-LAND-AREA-002", "Min. Contiguous Land (Urban ≥2.5 ac)", "Land & Title",         "CRIT", "RECORD"],
        ["AICTE-LAND-LEASE-003","Minimum Lease Period — 30 Years",      "Land & Title",         "CRIT", "RECORD"],
        ["AICTE-LAND-CONV-004", "Land Use Conversion Certificate",      "Land & Title",         "CRIT", "ISSUER"],
        ["AICTE-INFRA-PLAN-001","Approved Building Sanction Plan",       "Infrastructure",       "HIGH", "ISSUER"],
        ["AICTE-INFRA-OCC-002", "Occupancy Certificate",                "Infrastructure",       "HIGH", "ISSUER"],
        ["AICTE-FAC-FSR-001",   "Faculty:Student Ratio ≤ 1:15",         "Faculty & Cadre",      "HIGH", "RECORD"],
        ["AICTE-FAC-CADRE-002", "Faculty Cadre Ratio 1:2:6",            "Faculty & Cadre",      "MED",  "RECORD"],
        ["AICTE-SOC-REG-001",   "Society/Trust Registration — Valid",   "Institutional Reg.",   "CRIT", "ISSUER"],
        ["AICTE-FIN-FDR-001",   "Joint FDR Security Deposit ≥ ₹10L",   "Financial Compliance", "HIGH", "ISSUER"],
        ["AICTE-LAB-INV-001",   "Lab Equipment Count ≥ 20 per Lab",     "Infrastructure",       "MED",  "RECORD"],
        ["AICTE-ACC-DIV-001",   "Barrier-Free Accessibility (Divyangjan)","Safety & Compliance", "MED",  "ISSUER"],
        ["AICTE-ICT-NET-001",   "Internet Bandwidth ≥ 1 Mbps/student",  "ICT Infrastructure",   "LOW",  "RECORD"],
    ]
    r_tbl2 = Table(rules_hdr + rules_data,
                   colWidths=[3.8*cm, 5.5*cm, 3.5*cm, 1.4*cm, 2.6*cm])
    r_ts = base_table_style(C_NAVY)
    # Colour severity column
    sev_map = {"CRIT": C_ROSE, "HIGH": C_AMBER, "MED": C_INDIGO, "LOW": C_EMERALD}
    for i, row in enumerate(rules_data, 1):
        sev = row[3]
        clr = sev_map.get(sev, C_SLATE)
        r_ts.add("TEXTCOLOR",  (3,i), (3,i), clr)
        r_ts.add("FONTNAME",   (3,i), (3,i), "Helvetica-Bold")
    r_tbl2.setStyle(r_ts)
    story.append(r_tbl2)
    story.append(Spacer(1, 0.4*cm))

    story += section_heading("5.3  Rule Result Status Types", S, 2)
    status_hdr = [["Status", "Meaning"]]
    status_data = [
        ["PASS",                  "Logic true + trust gate satisfied with decisive evidence"],
        ["FAIL",                  "Logic evaluates to false"],
        ["UNVERIFIED",            "Logic true but trust gate blocked (evidence below minimum)"],
        ["SKIP",                  "Rule not applicable (e.g., wrong academic year)"],
        ["ERROR",                 "Safe evaluator or configuration error"],
    ]
    s_tbl = Table(status_hdr + status_data, colWidths=[4.5*cm, 12.3*cm])
    s_ts = base_table_style(C_NAVY)
    status_colours = {
        "PASS": C_EMERALD, "FAIL": C_ROSE,
        "UNVERIFIED": C_AMBER, "SKIP": C_SLATE, "ERROR": HexColor("#7C3AED"),
    }
    for i, row in enumerate(status_data, 1):
        clr = status_colours.get(row[0], C_SLATE)
        s_ts.add("TEXTCOLOR",  (0,i), (0,i), clr)
        s_ts.add("FONTNAME",   (0,i), (0,i), "Helvetica-Bold")
    s_tbl.setStyle(s_ts)
    story.append(s_tbl)

    story.append(PageBreak())

    # ── SECTION 6 — Forensics ─────────────────────────────────────────────────
    story += section_heading("Section 6 — Forensic Detection Capabilities", S, 1)

    story += section_heading("6.1  PDF Forensic Analysis (Structural)", S, 2)
    f1_data = [
        ["Technique",                "Method",                                           "Library"],
        ["Font diversity tampering", "FontTools extraction, entropy analysis",            "fonttools"],
        ["Incremental revision",     "Byte-stream inspection for appended updates",       "pypdf, pikepdf"],
        ["Whiteout concealment",     "OpenCV pixel analysis for white-on-white patches",  "pillow/opencv"],
        ["Metadata anomaly",         "XMP/Info dictionary inconsistency checks",          "pikepdf"],
        ["Structural PDF anomaly",   "Stream object analysis",                            "pypdf"],
    ]
    f1_tbl = Table(f1_data, colWidths=[4.5*cm, 8*cm, 4.3*cm])
    f1_tbl.setStyle(base_table_style(C_NAVY))
    story.append(f1_tbl)
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("6.2  Cryptographic Verification", S, 2)
    f2_data = [
        ["Check",                    "Method"],
        ["Digital signatures",       "pyHanko X.509 PKI verification against Root CA"],
        ["Authorized signatories",   "ISSUER_OFFICER role enforcement vs APPLICANT self-attestation"],
        ["Ed25519 QR payloads",      "Segno QR + public key registry verification"],
        ["C2PA content provenance",  "c2pa-python manifest validation"],
        ["SHA-256 audit chain",      "Append-only hash-chained ledger"],
    ]
    f2_tbl = Table(f2_data, colWidths=[4.5*cm, 12.3*cm])
    f2_tbl.setStyle(base_table_style(C_INDIGO))
    story.append(f2_tbl)
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("6.3  Geospatial & Physical Audit", S, 2)
    f3_data = [
        ["Check",                        "Method"],
        ["Campus geofencing",            "EXIF GPS extraction + Shapely polygon containment"],
        ["Declared boundary verification","GeoJSON campus polygon against submission coordinates"],
        ["Geotag-outside-campus",        "Point-in-polygon with configurable buffer zone"],
    ]
    f3_tbl = Table(f3_data, colWidths=[5*cm, 11.8*cm])
    f3_tbl.setStyle(base_table_style(C_NAVY))
    story.append(f3_tbl)
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("6.4  Cross-Application Fraud Detection (NetworkX)", S, 2)
    f4_data = [
        ["Pattern",                   "Detection Method"],
        ["Ghost faculty duplicates",  "Salted HMAC-SHA256 privacy-preserving matching across dossiers"],
        ["Photo reuse (faculty/lab)", "Perceptual hash (imagehash) comparison"],
        ["Seal reuse across institutions","Image similarity clustering"],
        ["Land/FDR pledge duplication","Graph edge deduplication across fraud graph nodes"],
        ["Fraud ring detection",      "NetworkX community detection / connected components"],
    ]
    f4_tbl = Table(f4_data, colWidths=[5*cm, 11.8*cm])
    f4_tbl.setStyle(base_table_style(C_INDIGO))
    story.append(f4_tbl)

    story.append(PageBreak())

    # ── SECTION 7 — Benchmark ─────────────────────────────────────────────────
    story += section_heading("Section 7 — Benchmark Evaluation Results", S, 1)

    meta = [
        ["Evaluation Date",    "2026-10-31"],
        ["Total Applications", "24 synthetic"],
        ["Dev Split",          "12 applications (Seed 42)"],
        ["Blind Split",        "12 applications (Seed 1337)"],
    ]
    meta_tbl = Table(meta, colWidths=[5*cm, 11.8*cm])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (0,-1), C_NAVY),
        ("TEXTCOLOR",    (0,0), (0,-1), C_WHITE),
        ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 7),
        ("GRID",         (0,0), (-1,-1), 0.4, C_SLATE_MID),
        ("ROWBACKGROUNDS",(1,0),(1,-1), [C_WHITE, C_SLATE_LT]),
        ("TEXTCOLOR",    (1,0), (1,-1), C_SLATE),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("7.1  Overall Performance Summary", S, 2)
    perf_hdr = [["Split", "Apps", "Clean", "False Alarms", "Precision", "Recall", "F1", "Runtime"]]
    perf_data = [
        ["Dev (Calibration)", "12", "2", "0.0%", "1.000", "1.000", "1.000", "8.13 s"],
        ["Blind (Held-Out)",  "12", "2", "0.0%", "1.000", "1.000", "1.000", "7.36 s"],
    ]
    p_tbl = Table(perf_hdr + perf_data,
                  colWidths=[3.8*cm, 1.2*cm, 1.2*cm, 2.5*cm, 2*cm, 1.6*cm, 1.6*cm, 2.9*cm])
    p_ts = base_table_style(C_NAVY)
    for r in [1, 2]:
        for c in [4, 5, 6]:
            p_ts.add("TEXTCOLOR",  (c,r), (c,r), C_EMERALD)
            p_ts.add("FONTNAME",   (c,r), (c,r), "Helvetica-Bold")
        p_ts.add("TEXTCOLOR", (3,r), (3,r), C_EMERALD)
        p_ts.add("FONTNAME",  (3,r), (3,r), "Helvetica-Bold")
    p_tbl.setStyle(p_ts)
    story.append(p_tbl)
    story.append(Spacer(1, 0.3*cm))

    story += section_heading("7.2  Per-Category Fraud Detection (Blind Split)", S, 2)
    cat_hdr = [["Fraud Category", "TP", "FP", "FN", "TN", "Precision", "Recall", "F1"]]
    cat_data = [
        ["expired_certificate",              "1","0","0","11","1.000","1.000","1.000"],
        ["edited_date_incremental_revision", "1","0","0","11","1.000","1.000","1.000"],
        ["font_mismatch",                    "1","0","0","11","1.000","1.000","1.000"],
        ["whiteout",                         "1","0","0","11","1.000","1.000","1.000"],
        ["invalid_or_applicant_signature",   "1","0","0","11","1.000","1.000","1.000"],
        ["tampered_qr",                      "1","0","0","11","1.000","1.000","1.000"],
        ["duplicate_faculty_ids",            "2","0","0","10","1.000","1.000","1.000"],
        ["reused_seal_and_lab_photo",        "2","0","0","10","1.000","1.000","1.000"],
        ["geotag_outside_campus",            "1","0","0","11","1.000","1.000","1.000"],
        ["scanned_hindi_documents",          "1","0","0","11","1.000","1.000","1.000"],
    ]
    c_tbl = Table(cat_hdr + cat_data,
                  colWidths=[5.5*cm, 0.8*cm, 0.8*cm, 0.8*cm, 0.8*cm, 2.1*cm, 1.8*cm, 1.8*cm])
    c_ts = base_table_style(C_NAVY)
    for r in range(1, len(cat_data)+1):
        for c in [5, 6, 7]:
            c_ts.add("TEXTCOLOR",  (c,r), (c,r), C_EMERALD)
            c_ts.add("FONTNAME",   (c,r), (c,r), "Helvetica-Bold")
        c_ts.add("BACKGROUND", (1,r), (3,r), C_EMERALD_LT)   # TP in green
        c_ts.add("FONTNAME",   (1,r), (1,r), "Helvetica-Bold")
    c_tbl.setStyle(c_ts)
    story.append(c_tbl)

    # Zero failures callout
    story.append(Spacer(1, 0.3*cm))
    callout_data = [["✅  ZERO FAILURES — All 10 planted fraud patterns flagged with 100% precision and recall across both splits."]]
    co_tbl = Table(callout_data, colWidths=[16.8*cm])
    co_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), C_EMERALD_LT),
        ("TEXTCOLOR",    (0,0), (-1,-1), HexColor("#065F46")),
        ("FONTNAME",     (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 10),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("GRID",         (0,0), (-1,-1), 1, C_EMERALD),
    ]))
    story.append(co_tbl)

    story.append(PageBreak())

    # ── SECTION 8 — Verification Pipeline ────────────────────────────────────
    story += section_heading("Section 8 — Verification Pipeline Methodology", S, 1)
    pipeline = [
        ("1. Sandboxed Ingestion",         "PDF quarantined in AES-GCM-256 encrypted store"),
        ("2. Forensic Scan",               "Structural anomalies, font diversity, whiteout, incremental revision"),
        ("3. Cryptographic Validation",    "pyHanko signature check, role enforcement, Ed25519 QR"),
        ("4. Physical & Geofence Audit",   "EXIF extraction, Shapely polygon containment"),
        ("5. Signed QR Verification",      "Ed25519 payload validation against trusted public key registry"),
        ("6. Cross-Application Fraud Graph","NetworkX ghost faculty, photo hashing, seal reuse"),
        ("7. Rules Engine Evaluation",     "Trust-gated YAML rules against extracted facts"),
        ("8. Advisory ML Annotation",      "YOLOX-M vision counting, OCR entity extraction (advisory only)"),
        ("9. Audit Ledger Commit",         "SHA-256 hash chain update"),
        ("10. Finding Aggregation",        "Pydantic v2 validated Finding objects with citations and evidence"),
    ]
    p_data = [[Paragraph(f"<b>{step}</b>", S["body"]),
               Paragraph(desc, S["body"])] for step, desc in pipeline]
    pip_tbl = Table(p_data, colWidths=[5*cm, 11.8*cm])
    pip_ts = TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 7),
        ("GRID",         (0,0), (-1,-1), 0.4, C_SLATE_MID),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [C_INDIGO_LT, C_WHITE]),
    ])
    # Number cells in dark navy
    for i in range(len(pipeline)):
        pip_ts.add("BACKGROUND", (0,i), (0,i), C_NAVY)
        pip_ts.add("TEXTCOLOR",  (0,i), (0,i), C_WHITE)
    pip_tbl.setStyle(pip_ts)
    story.append(pip_tbl)

    story.append(PageBreak())

    # ── SECTION 9 — Security ──────────────────────────────────────────────────
    story += section_heading("Section 9 — Security Architecture", S, 1)
    sec_data = [
        ["Security Control",          "Implementation"],
        ["Air-gap enforcement",       "Socket.connect() monkey-patch blocking non-loopback IPs"],
        ["Document quarantine",       "AES-GCM-256 encrypted quarantine spool"],
        ["Sandboxed parsing",         "Isolated subprocess with RLIMIT_AS, RLIMIT_CPU, timeout"],
        ["Safe expression evaluation","AST-based evaluator (no exec/eval)"],
        ["Audit integrity",           "SHA-256 append-only hash-chained ledger"],
        ["Rate limiting",             "RateLimitMiddleware per-IP"],
        ["Security headers",          "X-Content-Type-Options: nosniff, X-Frame-Options: DENY"],
        ["Offline indicator",         "X-Nirikshan-Offline: strict-airgap-local response header"],
        ["Auth",                      "JWT / session-based (routes_auth.py)"],
    ]
    sec_tbl = Table(sec_data, colWidths=[5*cm, 11.8*cm])
    sec_tbl.setStyle(base_table_style(C_NAVY))
    story.append(sec_tbl)

    story.append(PageBreak())

    # ── SECTION 10 — Data Models ──────────────────────────────────────────────
    story += section_heading("Section 10 — Data Models Summary", S, 1)

    for model_name, fields in [
        ("Finding", [
            "finding_id, rule_id, rule_name, category",
            "status: PASS | FAIL | INCONCLUSIVE | MANUAL_REVIEW_REQUIRED | FLAGGED_TAMPER",
            "summary, details, handbook_citation",
            "evidence_list: List[EvidenceItem]",
            "primary_bounding_box: BoundingBox (page, x, y, width, height)",
            "is_model_advisory_only, needs_verification",
            "Computed: highest_trust_level, evidence_level",
            "Model validator: auto-downgrades PASS/FAIL to MANUAL_REVIEW_REQUIRED if only advisory evidence",
        ]),
        ("EvidenceItem", [
            "evidence_id, trust_level, source_type, description, raw_value",
            "source_document_id, source_document_name, page_number, bounding_box",
            "is_self_attested (→ forces UNVERIFIED_CLAIM), is_tampered (→ caps at STRUCTURAL_FORENSIC)",
            "verification_method (e.g., PKI_X509, SUB_REGISTRAR_SEAL, OCR_ADVISORY)",
            "Computed: effective_trust_level(), trust_rank, is_decisive",
        ]),
        ("ApplicationDossier", [
            "dossier_id, institution_name, application_number, program, level",
            "institution_type, location_type, intake_proposed",
            "documents: List[DocumentRecord]",
            "findings: List[Finding]",
            "overall_status, risk_score (0–100), summary, extracted_params",
        ]),
    ]:
        story += section_heading(model_name, S, 2)
        story += bullets(fields, S)
        story.append(Spacer(1, 0.2*cm))

    story.append(PageBreak())

    # ── SECTION 11 — Dev & Quality ────────────────────────────────────────────
    story += section_heading("Section 11 — Development & Quality", S, 1)

    story += section_heading("Testing Infrastructure", S, 2)
    story += bullets([
        "pytest + pytest-asyncio (async test mode)",
        "httpx for integration testing",
        "Playwright for E2E frontend tests",
        "Vitest + Testing Library for unit/component tests",
    ], S)

    story += section_heading("Code Quality", S, 2)
    story += bullets([
        "ruff (linting): E, F, W, I, N, UP, B, A, C4, PT, RET, SIM rules; line length 100",
        "mypy (strict type checking): Python 3.11, pydantic plugin, no_implicit_optional",
        "Target: Python 3.11 / TypeScript 5.7",
    ], S)

    story += section_heading("CI/CD", S, 2)
    story += bullets([
        "GitHub Actions (.github/workflows/ci.yml)",
        "Docker + docker-compose deployment",
        "Makefile / make.ps1 (Windows) cross-platform build scripts",
    ], S)

    story.append(PageBreak())

    # ── SECTION 12 — Improvements ─────────────────────────────────────────────
    story += section_heading("Section 12 — Identified Areas for Improvement", S, 1)
    improvements = [
        ("Benchmark on Real Data",
         "Synthetic benchmarks show 100% F1; real-world document quality, edge cases "
         "(partial tamper, multilingual docs) should be tested.", C_AMBER_LT),
        ("YAML Ruleset Completeness",
         "Several rules have needs_verification: true and page: \"TODO\" — handbook citations "
         "must be finalized before production deployment.", C_ROSE_LT),
        ("ML Model Hardening",
         "ONNX runtime inference path for YOLOX-M vision model needs integration tests "
         "and adversarial robustness evaluation.", C_AMBER_LT),
        ("Multilingual OCR",
         "Hindi/regional language scanned document support (flagged as scanned_hindi_documents "
         "fraud category) needs dedicated OCR pipeline.", C_ROSE_LT),
        ("Audit Replay Coverage",
         "Deterministic replay verification should have an automated regression test to prevent "
         "hash chain drift across versions.", C_AMBER_LT),
        ("Frontend Accessibility",
         "WCAG 2.1 AA compliance check needed for officer console (ironically, given the "
         "Divyangjan accessibility rule the system enforces).", C_ROSE_LT),
        ("API Rate Limiting Tuning",
         "Current in-memory rate limiter should use Redis for multi-instance deployments.", C_AMBER_LT),
    ]
    for idx, (title, desc, bg) in enumerate(improvements, 1):
        row = [[
            Paragraph(f"<b>{idx}.  {title}</b>", S["h3"]),
            Paragraph(desc, S["body"]),
        ]]
        tbl = Table(row, colWidths=[5.2*cm, 11.6*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), bg),
            ("GRID",         (0,0), (-1,-1), 0.4, C_SLATE_MID),
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
            ("TOPPADDING",   (0,0), (-1,-1), 7),
            ("BOTTOMPADDING",(0,0), (-1,-1), 7),
            ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.15*cm))

    story.append(PageBreak())

    # ── APPENDIX A — Repo Structure ───────────────────────────────────────────
    story += section_heading("Appendix A — Repository Structure", S, 1)
    repo_tree = """\
nirikshan/
├── backend/
│   ├── nirikshan/
│   │   ├── advisory/     # ML: YOLOX-M, Ask-Why, entity extraction
│   │   ├── api/          # 10 FastAPI route modules
│   │   ├── core/         # Config, DB, safe_eval, rule_schema
│   │   ├── engine/       # Audit log, hash chain, replay
│   │   ├── fraud/        # NetworkX fraud graph
│   │   ├── ingest/       # PDF extractor, font analysis, rasterizer
│   │   ├── rules/        # Rules engine, loader, aliases
│   │   ├── sandbox/      # Sandboxed worker, quarantine
│   │   ├── schemas/      # Pydantic v2 models
│   │   ├── trust/        # Trust ladder
│   │   └── worker/       # Async job service
│   ├── rulesets/         # AICTE APH YAML rules
│   ├── tests/            # pytest test suite
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── api/          # Typed REST client, hooks, schema
│       ├── components/   # UI components
│       ├── pages/        # Officer, Applicant, Login, Landing
│       └── context/      # Auth, Theme
├── docs/                 # Architecture specs
└── docker-compose.yml"""

    for line in repo_tree.split("\n"):
        story.append(Paragraph(line.replace(" ", "&nbsp;"), S["code"]))

    return story


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm,
        topMargin=2*cm,
        bottomMargin=2.8*cm,
        title="Nirikshan — Comprehensive Project Analysis Report",
        author="Nirikshan Dev Team",
        subject="AICTE Regulatory Scrutiny Platform",
    )

    S = build_styles()
    on_first, on_later = _make_page_callbacks(doc)

    # Build full story
    story = []

    # Cover page (uses first-page callback = no footer)
    story += cover_page(S)

    # Content pages
    story += build_story(S)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    print(f"[OK] PDF generated: {OUTPUT_PATH}")
    print(f"[OK] File size:     {os.path.getsize(OUTPUT_PATH):,} bytes")


if __name__ == "__main__":
    main()
