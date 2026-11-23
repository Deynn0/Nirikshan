"""Generate the exact fixtures dataset hierarchy requested by the user:

fixtures/
├── out/
│   ├── A1/
│   ├── A2/
│   ├── A3/
│   ├── A4/
│   ├── A5/
│   ├── A6/
│   ├── A7/
│   ├── A8/
│   ├── A9/
│   ├── A10/
│   ├── A11/
│   ├── rectification/
│   ├── scan/
│   ├── trust/
│   └── manifest.json
└── real/
    ├── photos/
    └── manifest.json
"""

from __future__ import annotations

import io
import json
import random
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from scripts.make_fixtures import (
    generate_synthetic_font,
    make_circular_seal,
    make_clean_document,
    make_degraded_scanned_hindi_doc,
    make_expired_cert_document,
    make_font_mismatch_document,
    make_incremental_revision_document,
    make_signed_pdf_document,
    make_signed_qr_code,
    make_synthetic_photo,
    make_whiteout_document,
    setup_crypto_infrastructure,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ExifTags
import imagehash


def generate_fixtures_tree(fixtures_root: Path) -> None:
    fixtures_root.mkdir(parents=True, exist_ok=True)
    out_dir = fixtures_root / "out"
    real_dir = fixtures_root / "real"

    out_dir.mkdir(parents=True, exist_ok=True)
    real_dir.mkdir(parents=True, exist_ok=True)

    # 1. Setup Trust Infrastructure under fixtures/out/trust
    trust_dir = out_dir / "trust"
    trust_dir.mkdir(parents=True, exist_ok=True)
    crypto_infra = setup_crypto_infrastructure(trust_dir)

    # Copy / generate issuers.yaml
    issuers_yaml_path = trust_dir / "issuers.yaml"
    issuers_yaml_content = """# Nirikshan Authorized Trust Anchors & Issuers
issuers:
  - id: aicte-central
    name: "All India Council for Technical Education"
    role: "REGULATORY_BODY"
    ca_cert: "trust_ca.pem"
    crl_url: "http://crl.aicte-india.org/root.crl"
    status: "ACTIVE"
  - id: delhi-fire-service
    name: "Delhi Fire and Rescue Services"
    role: "STATUTORY_AUTHORITY"
    ca_cert: "trust_ca.pem"
    status: "ACTIVE"
  - id: delhi-revenue-dept
    name: "State Revenue Department - Land Administration"
    role: "REVENUE_AUTHORITY"
    ca_cert: "trust_ca.pem"
    status: "ACTIVE"
"""
    issuers_yaml_path.write_text(issuers_yaml_content, encoding="utf-8")

    # Generate custom font for synthetic mismatch / Devanagari in trust/fonts
    fonts_dir = trust_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    font_path = fonts_dir / "SyntheticMismatchFont.ttf"
    generate_synthetic_font(font_path, "SyntheticMismatchFont")
    try:
        pdfmetrics.registerFont(TTFont("SyntheticMismatchFont", str(font_path)))
    except Exception:
        pass

    # Shared assets between A9 and A10
    shared_assets_dir = out_dir / "_shared_assets"
    shared_assets_dir.mkdir(parents=True, exist_ok=True)
    shared_lab_photo_path = shared_assets_dir / "physics_lab_shared.jpg"
    shared_seal_path = shared_assets_dir / "registrar_seal_shared.png"

    shared_photo_phash = make_synthetic_photo(
        shared_lab_photo_path,
        "Advanced Physics Lab - Optical Bench",
        28.6180,
        77.2150,
        style="physics_lab",
    )
    shared_seal_phash = make_circular_seal(
        shared_seal_path, "Delhi State Revenue Dept", "Delhi", seal_type="registrar"
    )
    shared_faculty_aadhaar = "9988 7766 5544"

    # Define Application Configurations for A1 through A11
    apps_meta: dict[str, dict] = {}
    
    scenarios = [
        ("A1", "Clean Engineering Application", True, []),
        ("A2", "Clean Pharmacy Application", True, []),
        ("A3", "Expired Fire Safety NOC", False, ["expired_certificate"]),
        ("A4", "Incremental Revision Order Tampering", False, ["edited_date_incremental_revision"]),
        ("A5", "Font Splicing & Size Discontinuity", False, ["font_mismatch"]),
        ("A6", "Building Sanction Whiteout Concealment", False, ["whiteout"]),
        ("A7", "Unauthorized Applicant Self-Signature", False, ["invalid_or_applicant_signature"]),
        ("A8", "Cryptographically Tampered QR Code", False, ["tampered_qr"]),
        ("A9", "Duplicate Faculty & Shared Lab Infrastructure (Part 1)", False, ["duplicate_faculty_ids", "reused_seal_and_lab_photo"]),
        ("A10", "Cross-Institution Photo & Seal Reuse (Part 2)", False, ["reused_seal_and_lab_photo", "duplicate_faculty_ids"]),
        ("A11", "Geotag Outside Declared Campus Boundary", False, ["geotag_outside_campus"]),
    ]

    for app_id, title, is_clean, frauds in scenarios:
        app_dir = out_dir / app_id
        docs_dir = app_dir / "documents"
        photos_dir = app_dir / "photos"
        docs_dir.mkdir(parents=True, exist_ok=True)
        photos_dir.mkdir(parents=True, exist_ok=True)

        inst_name = f"Institute of Technology & Science ({app_id})"
        app_no = f"AICTE/2024/APP/{app_id}"

        campus_poly = [
            [77.2000, 28.6100],
            [77.2200, 28.6100],
            [77.2200, 28.6250],
            [77.2000, 28.6250],
        ]

        extracted_params: dict = {
            "land_area_acres": 4.5,
            "is_contiguous": True,
            "survey_no": "104/1A",
            "built_up_area_sqm": 12500.0,
            "fire_noc_expired": False,
            "faculty_count": 60,
            "faculty": [],
            "photos": [],
            "seals": [],
        }

        if app_id == "A1":
            make_clean_document(
                docs_dir / "land_deed.pdf",
                "REGISTERED LAND SALE DEED",
                inst_name,
                app_no,
                ["Freehold clear title of 4.50 acres verified.", "Survey Number: 104/1A.", "Encumbrance free for 30 years."],
            )
            make_clean_document(
                docs_dir / "fire_noc.pdf",
                "FIRE SAFETY CLEARANCE CERTIFICATE",
                inst_name,
                app_no,
                ["Fire fighting system fully operational.", "Certificate valid through 2026-12-31."],
            )
            make_signed_pdf_document(
                docs_dir / "approval_letter.pdf",
                inst_name,
                app_no,
                signer_key=crypto_infra["officer"][0],
                signer_cert=crypto_infra["officer"][1],
                root_ca=crypto_infra["asn1_ca"],
            )
            make_signed_qr_code(
                photos_dir / "approval_qr.png",
                {"institution": inst_name, "app_no": app_no, "land_acres": 4.5},
                priv_key=crypto_infra["qr_priv_key"],
                key_id=crypto_infra["qr_key_id"],
            )
            p_hash = make_synthetic_photo(
                photos_dir / "computer_lab.jpg",
                "Computer Center",
                28.6145,
                77.2085,
                style="computer_lab",
            )
            s_hash = make_circular_seal(photos_dir / "fire_service_seal.png", "Delhi Fire Service", "Delhi", seal_type="fire_service")
            extracted_params["photos"].append({"phash": p_hash, "type": "COMPUTER_LAB"})
            extracted_params["seals"].append({"phash": s_hash, "issuing_authority": "Delhi Fire Service"})
            extracted_params["faculty"].append({
                "aadhaar": "4521 8832 1092",
                "name": "Dr. Sunil Kumar",
                "employment_type": "FULL_TIME",
                "periods": ["2024-2025"],
            })

        elif app_id == "A2":
            make_clean_document(
                docs_dir / "land_deed.pdf",
                "REGISTERED LAND SALE DEED",
                inst_name,
                app_no,
                ["Land area 3.20 acres contiguous freehold title.", "Survey Number: 88/2.", "Approved educational usage."],
            )
            make_clean_document(
                docs_dir / "fire_noc.pdf",
                "STATE FIRE SAFETY NOC",
                inst_name,
                app_no,
                ["State Disaster Management compliance certified.", "Validity period: 2024-01-01 to 2026-12-31."],
            )
            make_signed_pdf_document(
                docs_dir / "sanction_order.pdf",
                inst_name,
                app_no,
                signer_key=crypto_infra["officer"][0],
                signer_cert=crypto_infra["officer"][1],
                root_ca=crypto_infra["asn1_ca"],
            )
            make_signed_qr_code(
                photos_dir / "approval_qr.png",
                {"institution": inst_name, "app_no": app_no, "land_acres": 3.2},
                priv_key=crypto_infra["qr_priv_key"],
                key_id=crypto_infra["qr_key_id"],
            )
            p_hash = make_synthetic_photo(
                photos_dir / "chemistry_lab.jpg",
                "Pharmaceutical Chemistry Lab",
                28.6160,
                77.2100,
                style="chemistry_lab",
            )
            s_hash = make_circular_seal(photos_dir / "municipal_seal.png", "Municipal Corporation", "Delhi", seal_type="municipal")
            extracted_params["photos"].append({"phash": p_hash, "type": "CHEMISTRY_LAB"})
            extracted_params["seals"].append({"phash": s_hash, "issuing_authority": "Municipal Corporation"})

        elif app_id == "A3":
            extracted_params["fire_noc_expired"] = True
            make_expired_cert_document(docs_dir / "fire_safety_noc.pdf", inst_name, app_no)
            make_clean_document(
                docs_dir / "land_deed.pdf",
                "REGISTERED LAND DEED",
                inst_name,
                app_no,
                ["Survey Number 104/1A.", "Clear Title."],
            )

        elif app_id == "A4":
            make_incremental_revision_document(docs_dir / "land_conversion_order.pdf", inst_name, app_no)
            make_clean_document(
                docs_dir / "fire_noc.pdf",
                "FIRE SAFETY NOC",
                inst_name,
                app_no,
                ["Valid through 2026-12-31."],
            )

        elif app_id == "A5":
            make_font_mismatch_document(docs_dir / "land_deed.pdf", inst_name, app_no, "SyntheticMismatchFont")

        elif app_id == "A6":
            make_whiteout_document(docs_dir / "building_sanction.pdf", inst_name, app_no)

        elif app_id == "A7":
            make_signed_pdf_document(
                docs_dir / "official_sanction.pdf",
                inst_name,
                app_no,
                signer_key=crypto_infra["applicant"][0],
                signer_cert=crypto_infra["applicant"][1],
                root_ca=crypto_infra["asn1_ca"],
            )

        elif app_id == "A8":
            make_signed_qr_code(
                photos_dir / "verification_qr.png",
                {"institution": inst_name, "app_no": app_no, "land_acres": 4.5},
                priv_key=crypto_infra["qr_priv_key"],
                key_id=crypto_infra["qr_key_id"],
                tamper=True,
            )

        elif app_id == "A9":
            extracted_params["faculty"].append({
                "aadhaar": shared_faculty_aadhaar,
                "name": "Dr. Ramesh Sharma (Shared Faculty)",
                "employment_type": "FULL_TIME",
                "periods": ["2024-2025"],
                "designation": "Professor & HOD",
            })
            extracted_params["photos"].append({
                "phash": shared_photo_phash,
                "type": "PHYSICS_LAB",
                "source_path": str(shared_lab_photo_path.relative_to(fixtures_root)),
            })
            extracted_params["seals"].append({
                "phash": shared_seal_phash,
                "issuing_authority": "Delhi State Revenue Dept",
                "source_path": str(shared_seal_path.relative_to(fixtures_root)),
            })
            # Copy shared files locally
            (photos_dir / "physics_lab.jpg").write_bytes(shared_lab_photo_path.read_bytes())
            (photos_dir / "revenue_seal.png").write_bytes(shared_seal_path.read_bytes())

        elif app_id == "A10":
            extracted_params["faculty"].append({
                "aadhaar": shared_faculty_aadhaar,
                "name": "Dr. Ramesh Sharma (Shared Faculty)",
                "employment_type": "FULL_TIME",
                "periods": ["2024-2025"],
                "designation": "Professor",
            })
            extracted_params["photos"].append({
                "phash": shared_photo_phash,
                "type": "PHYSICS_LAB",
                "source_path": str(shared_lab_photo_path.relative_to(fixtures_root)),
            })
            extracted_params["seals"].append({
                "phash": shared_seal_phash,
                "issuing_authority": "Pune Municipal Corporation (Reused Seal)",
                "source_path": str(shared_seal_path.relative_to(fixtures_root)),
            })
            # Copy shared files locally
            (photos_dir / "physics_lab.jpg").write_bytes(shared_lab_photo_path.read_bytes())
            (photos_dir / "revenue_seal.png").write_bytes(shared_seal_path.read_bytes())

        elif app_id == "A11":
            # Photo taken 55 km away outside campus boundary
            p_hash = make_synthetic_photo(
                photos_dir / "site_photo.jpg",
                "Main Campus Exterior",
                28.1500,
                76.8000,
                style="computer_lab",
            )
            extracted_params["photos"].append({"phash": p_hash, "type": "CAMPUS_EXTERIOR"})

        app_meta = {
            "application_id": app_id,
            "title": title,
            "institution_name": inst_name,
            "application_number": app_no,
            "is_clean": is_clean,
            "planted_frauds": frauds,
            "campus_polygon": campus_poly,
            "extracted_params": extracted_params,
            "files": {
                "documents": [p.name for p in docs_dir.glob("*.pdf")],
                "photos": [p.name for p in photos_dir.glob("*.*")],
            },
        }
        (app_dir / "meta.json").write_text(json.dumps(app_meta, indent=2), encoding="utf-8")
        apps_meta[app_id] = app_meta

    # 2. Build fixtures/out/rectification
    rect_dir = out_dir / "rectification"
    rect_dir.mkdir(parents=True, exist_ok=True)

    make_clean_document(
        rect_dir / "rectification_notice.pdf",
        "AICTE COMPLIANCE RECTIFICATION NOTICE",
        "Apex Educational Institute",
        "AICTE/RECT/2024/091",
        [
            "Discrepancy noted during initial scrutiny: Fire Safety NOC expired.",
            "Rectification required: Upload valid renewed Fire Safety Certificate within 15 calendar days.",
            "Authorized Scrutiny Desk: North-Western Regional Bureau.",
        ],
    )
    make_clean_document(
        rect_dir / "remedial_fire_noc.pdf",
        "RENEWED FIRE SAFETY CLEARANCE CERTIFICATE",
        "Apex Educational Institute",
        "AICTE/RECT/2024/091",
        [
            "State Fire Services inspected premises on 2024-10-01.",
            "All deficiencies resolved. Certificate issued with unconditional validity through 2027-09-30.",
        ],
    )

    rect_thread = {
        "thread_id": "rect-thread-9821",
        "application_id": "A3",
        "status": "UNDER_REVIEW",
        "messages": [
            {
                "sender": "OFFICER",
                "timestamp": "2024-10-10T09:30:00Z",
                "message": "Fire NOC submitted is expired as of 2022-12-31. Please upload valid certificate.",
                "attachment": "rectification_notice.pdf",
            },
            {
                "sender": "APPLICANT",
                "timestamp": "2024-10-14T14:15:00Z",
                "message": "Renewed Fire NOC obtained from State Fire Department attached herewith.",
                "attachment": "remedial_fire_noc.pdf",
            },
        ],
    }
    (rect_dir / "thread.json").write_text(json.dumps(rect_thread, indent=2), encoding="utf-8")

    # 3. Build fixtures/out/scan
    scan_dir = out_dir / "scan"
    scan_dir.mkdir(parents=True, exist_ok=True)

    make_degraded_scanned_hindi_doc(
        scan_dir / "khatauni_revenue_hi_scanned.pdf",
        "State Revenue Office - Land Title Record",
        font_path=font_path,
    )

    # Scanned image-only stub
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.showPage()
    c.save()
    (scan_dir / "scanned_stub_image_only.pdf").write_bytes(buf.getvalue())

    # 4. Save fixtures/out/manifest.json
    out_manifest = {
        "version": "1.0.0",
        "type": "synthetic_scrutiny_fixtures",
        "total_applications": len(apps_meta),
        "applications": apps_meta,
        "special_suites": {
            "rectification": ["rectification_notice.pdf", "remedial_fire_noc.pdf"],
            "scan": ["khatauni_revenue_hi_scanned.pdf", "scanned_stub_image_only.pdf"],
            "trust": ["trust_ca.der", "trust_ca.pem", "keyring.json", "issuers.yaml"],
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(out_manifest, indent=2), encoding="utf-8")

    # Clean up temporary shared assets directory if desired
    import shutil
    if shared_assets_dir.exists():
        shutil.rmtree(shared_assets_dir)

    # 5. Build fixtures/real
    real_photos_dir = real_dir / "photos"
    real_photos_dir.mkdir(parents=True, exist_ok=True)

    real_photos_metadata = []
    photo_definitions = [
        ("campus_entrance.jpg", "Campus Main Administrative Gate", 28.6139, 77.2090, "computer_lab"),
        ("computer_center.jpg", "High Performance Computing Lab", 28.6142, 77.2094, "computer_lab"),
        ("chemistry_lab.jpg", "Applied Chemistry Research Lab", 28.6146, 77.2088, "chemistry_lab"),
        ("central_library.jpg", "Central Academic Library", 28.6150, 77.2082, "library"),
        ("physics_lab.jpg", "Laser Optics and Sensor Lab", 28.6140, 77.2099, "physics_lab"),
    ]

    for fname, desc, lat, lon, style in photo_definitions:
        target_path = real_photos_dir / fname
        phash = make_synthetic_photo(
            target_path,
            desc,
            lat,
            lon,
            style=style,
        )
        real_photos_metadata.append({
            "filename": fname,
            "description": desc,
            "latitude": lat,
            "longitude": lon,
            "perceptual_hash": phash,
            "has_c2pa_manifest": False,
            "exif_verified": True,
        })

    # Save fixtures/real/manifest.json
    real_manifest = {
        "version": "1.0.0",
        "type": "real_inspection_photos_manifest",
        "total_photos": len(real_photos_metadata),
        "photos": real_photos_metadata,
    }
    (real_dir / "manifest.json").write_text(json.dumps(real_manifest, indent=2), encoding="utf-8")

    print("[SUCCESS] Successfully created fixtures dataset structure:")
    print(f"          Root: {fixtures_root}")
    print(f"          Out Applications: {list(apps_meta.keys())}")
    print(f"          Rectification, Scan, Trust, and Real Photos populated.")


def main() -> None:
    # Target workspace root fixtures
    workspace_fixtures = BACKEND_DIR.parent / "fixtures"
    generate_fixtures_tree(workspace_fixtures)


if __name__ == "__main__":
    main()
