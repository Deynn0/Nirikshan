"""Tests for cross-application fraud graph, detectors, PII salting, and Cytoscape.js API.

Verifies:
1. Planted fraud patterns (Ghost Faculty, Certificate Sharing, Photo Reuse, Seal Reuse) are accurately detected.
2. Clean control set yields ZERO false positives.
3. Plaintext Aadhaar/PAN is NEVER stored (salted HMAC-SHA256 only).
4. Incremental database updates function correctly.
5. API endpoints return valid Cytoscape.js JSON with cluster IDs and severities.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from nirikshan.db.session import init_db
from nirikshan.fraud import (
    CertificateSharingDetector,
    EntityExtractor,
    EntityType,
    FraudDetectorEngine,
    GhostFacultyDetector,
    PhotoReuseDetector,
    SealReuseDetector,
    fraud_service,
    hamming_distance,
    hash_salted_identity,
    mask_identity_label,
    normalize_identity_id,
)
from nirikshan.main import app
from nirikshan.schemas.finding import VerificationStatus


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    """Ensure database schema is created prior to test requests."""
    await init_db()


# ==============================================================================
# 1. PII SALTING AND IDENTITY TESTS
# ==============================================================================

def test_aadhaar_pan_salting_never_stores_plaintext() -> None:
    """Assert Aadhaar and PAN numbers are converted to HMAC-SHA256 salted hashes and never stored raw."""
    raw_aadhaar = "1234 5678 9012"
    raw_pan = "abcde1234f"

    # Normalization
    assert normalize_identity_id(raw_aadhaar) == "123456789012"
    assert normalize_identity_id(raw_pan) == "ABCDE1234F"

    # Salted hashes
    salt_1 = "test-salt-secret-alpha"
    salt_2 = "test-salt-secret-beta"

    hash_a1 = hash_salted_identity(raw_aadhaar, salt=salt_1)
    hash_a2 = hash_salted_identity(raw_aadhaar, salt=salt_2)

    # 64-char hex digest
    assert len(hash_a1) == 64
    assert len(hash_a2) == 64
    # Plaintext must not be present in hash
    assert "1234" not in hash_a1 or raw_aadhaar not in hash_a1
    assert hash_a1 != hash_a2  # Different salts yield different hashes

    # Masking for visual display only
    assert mask_identity_label(raw_aadhaar) == "XXXX-XXXX-9012"
    assert mask_identity_label(raw_pan) == "XXXXXX234F"


def test_hamming_distance_calculation() -> None:
    """Verify bitwise Hamming distance between perceptual hash strings."""
    # Identical hashes
    assert hamming_distance("8000000000000000", "8000000000000000") == 0
    # 1 bit difference (0x0 vs 0x1)
    assert hamming_distance("8000000000000000", "8000000000000001") == 1
    # 2 bits difference (0x0 vs 0x3)
    assert hamming_distance("8000000000000000", "8000000000000003") == 2
    # None or empty returns 64
    assert hamming_distance(None, "8000000000000000") == 64


# ==============================================================================
# 2. PLANTED FRAUD FIXTURES & DETECTOR TESTS
# ==============================================================================

def test_ghost_faculty_detector_planted_fraud() -> None:
    """Test Ghost Faculty detector finds full-time faculty declared at 2+ institutions overlapping."""
    extractor = EntityExtractor(salt="test-fraud-salt-2024")
    fac_aadhaar = "9988 7766 5544"

    # App 1: Apex College claims Faculty as Full-Time (2024-2025)
    app1 = extractor.extract_from_dossier_data(
        dossier_id="dos-app-01",
        application_number="APP-APEX-001",
        institution_name="Apex Institute of Technology",
        extracted_params={
            "faculty": [
                {
                    "aadhaar": fac_aadhaar,
                    "name": "Dr. Ramesh Sharma",
                    "employment_type": "FULL_TIME",
                    "periods": ["2024-2025"],
                    "designation": "Professor",
                }
            ]
        },
    )

    # App 2: Beacon Institute claims same Faculty as Full-Time (2024-2025)
    app2 = extractor.extract_from_dossier_data(
        dossier_id="dos-app-02",
        application_number="APP-BEACON-002",
        institution_name="Beacon Engineering College",
        extracted_params={
            "faculty": [
                {
                    "aadhaar": fac_aadhaar,
                    "name": "Dr. Ramesh Sharma",
                    "employment_type": "FULL_TIME",
                    "periods": ["2024-2025"],
                    "designation": "Professor & HOD",
                }
            ]
        },
    )

    # Verify entity has salted hash and NOT raw Aadhaar
    fac_ent = [e for e in app1.entities if e.entity_type == EntityType.FACULTY][0]
    assert fac_ent.entity_value == hash_salted_identity(fac_aadhaar, salt="test-fraud-salt-2024")
    assert fac_aadhaar not in fac_ent.entity_value

    # Run Ghost Faculty Detector
    findings = GhostFacultyDetector.detect([
        {"dossier_id": app1.dossier_id, "institution_name": app1.institution_name, "entities": app1.entities},
        {"dossier_id": app2.dossier_id, "institution_name": app2.institution_name, "entities": app2.entities},
    ])

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "AICTE-FRAUD-GHOST-FACULTY"
    assert f.status == VerificationStatus.FLAGGED_TAMPER
    assert "dos-app-01" in f.advisory_notes[0]
    assert "dos-app-02" in f.advisory_notes[0]
    assert len(f.evidence_list) == 2


def test_certificate_sharing_detector_planted_fraud() -> None:
    """Test Certificate Sharing detector detects same Fire NOC or Land Deed across institutions."""
    extractor = EntityExtractor(salt="test-fraud-salt-2024")
    shared_fire_noc = "FIRE-NOC/2024/DELHI/8821"

    app1 = extractor.extract_from_dossier_data(
        dossier_id="dos-cert-01",
        application_number="APP-CERT-001",
        institution_name="City Technical College",
        extracted_params={"fire_noc_number": shared_fire_noc},
    )

    app2 = extractor.extract_from_dossier_data(
        dossier_id="dos-cert-02",
        application_number="APP-CERT-002",
        institution_name="Metro Institute of Science",
        extracted_params={"fire_noc_number": shared_fire_noc},
    )

    findings = CertificateSharingDetector.detect([
        {"dossier_id": app1.dossier_id, "institution_name": app1.institution_name, "entities": app1.entities},
        {"dossier_id": app2.dossier_id, "institution_name": app2.institution_name, "entities": app2.entities},
    ])

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "AICTE-FRAUD-CERT-SHARING"
    assert f.status == VerificationStatus.FLAGGED_TAMPER
    assert "dos-cert-01" in f.advisory_notes[0]
    assert "dos-cert-02" in f.advisory_notes[0]


def test_photo_reuse_detector_planted_fraud() -> None:
    """Test Photo Reuse detector detects near-identical lab photos within Hamming distance threshold."""
    extractor = EntityExtractor()

    # App 1: uploads physics lab photo with pHash 1
    phash_1 = "a1b2c3d4e5f60718"
    app1 = extractor.extract_from_dossier_data(
        dossier_id="dos-photo-01",
        application_number="APP-PH-001",
        institution_name="Sunrise College of Engineering",
        extracted_params={
            "photos": [{"phash": phash_1, "type": "PHYSICS_LAB", "description": "General Physics Lab"}]
        },
    )

    # App 2: uploads near-identical photo (distance = 1, e.g. last nibble differs by 1 bit: 8 vs 9)
    # 0x8 = 1000b, 0x9 = 1001b -> distance is exactly 1 bit
    phash_2 = "a1b2c3d4e5f60719"
    assert hamming_distance(phash_1, phash_2) == 1

    app2 = extractor.extract_from_dossier_data(
        dossier_id="dos-photo-02",
        application_number="APP-PH-002",
        institution_name="Horizon Institute of Technology",
        extracted_params={
            "photos": [{"phash": phash_2, "type": "CHEMISTRY_LAB", "description": "Chemistry Setup"}]
        },
    )

    findings = PhotoReuseDetector.detect(
        [
            {"dossier_id": app1.dossier_id, "institution_name": app1.institution_name, "entities": app1.entities},
            {"dossier_id": app2.dossier_id, "institution_name": app2.institution_name, "entities": app2.entities},
        ],
        threshold=6,
    )

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "AICTE-FRAUD-PHOTO-REUSE"
    assert f.status == VerificationStatus.FLAGGED_TAMPER
    assert "dos-photo-01" in f.advisory_notes[0]
    assert "dos-photo-02" in f.advisory_notes[0]


def test_seal_reuse_detector_planted_fraud() -> None:
    """Test Seal Reuse detector catches identical seal pHash claimed across DIFFERENT issuing authorities."""
    extractor = EntityExtractor()
    seal_phash = "f0e1d2c3b4a59687"

    # App 1: Seal from Delhi Fire Service
    app1 = extractor.extract_from_dossier_data(
        dossier_id="dos-seal-01",
        application_number="APP-SEAL-001",
        institution_name="Delhi Engineering Institute",
        extracted_params={
            "seals": [{"phash": seal_phash, "issuing_authority": "Delhi Fire Service"}]
        },
    )

    # App 2: Same seal claimed from Sub-Registrar Office Pune
    app2 = extractor.extract_from_dossier_data(
        dossier_id="dos-seal-02",
        application_number="APP-SEAL-002",
        institution_name="Pune Polytechnic",
        extracted_params={
            "seals": [{"phash": seal_phash, "issuing_authority": "Sub-Registrar Office Pune"}]
        },
    )

    findings = SealReuseDetector.detect(
        [
            {"dossier_id": app1.dossier_id, "institution_name": app1.institution_name, "entities": app1.entities},
            {"dossier_id": app2.dossier_id, "institution_name": app2.institution_name, "entities": app2.entities},
        ],
        threshold=5,
    )

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "AICTE-FRAUD-SEAL-REUSE"
    assert f.status == VerificationStatus.FLAGGED_TAMPER
    assert "dos-seal-01" in f.advisory_notes[0]
    assert "dos-seal-02" in f.advisory_notes[0]


# ==============================================================================
# 3. CLEAN CONTROL SET (ZERO FALSE POSITIVES)
# ==============================================================================

def test_clean_control_set_zero_false_positives() -> None:
    """Assert ZERO fraud findings on legitimate multi-application control set:

    - Non-overlapping career progression (Faculty works at A then later moves to B)
    - Part-time / Visiting faculty legitimate multi-institution teaching
    - Unique Fire NOCs & Land records
    - Distinct photos (Hamming distance > 25)
    - Same issuing authority on valid documents (Delhi Fire Service stamping 2 colleges)
    """
    extractor = EntityExtractor(salt="control-set-salt-2024")

    # College A: Compliant Engineering College
    fac_a_id = "1111 2222 3333"
    app_a = extractor.extract_from_dossier_data(
        dossier_id="dos-clean-01",
        application_number="APP-CLEAN-01",
        institution_name="Clean Valley College of Engineering",
        extracted_params={
            "faculty": [
                {
                    "aadhaar": fac_a_id,
                    "name": "Prof. Amit Verma",
                    "employment_type": "FULL_TIME",
                    "periods": ["2024-2025"],
                },
                {
                    "aadhaar": "4444 5555 6666",
                    "name": "Dr. Sunita Rao",
                    "employment_type": "VISITING",  # Visiting faculty!
                    "periods": ["2024-2025"],
                },
            ],
            "fire_noc_number": "NOC/FIRE/DEL/2024/1111",
            "photos": [
                {"phash": "00000000ffffffff", "type": "LAB", "description": "Electronics Lab A"}
            ],
            "seals": [
                {"phash": "1234567812345678", "issuing_authority": "Delhi Fire Service"}
            ],
        },
    )

    # College B: Compliant Pharmacy Institute
    # Dr. Sunita Rao also visits here (Permissible under AICTE 20% Visiting Norms)
    # Prof. Amit Verma does NOT work here; faculty here is Dr. Neha Patel
    # Delhi Fire Service issued their NOC with its legitimate official seal
    app_b = extractor.extract_from_dossier_data(
        dossier_id="dos-clean-02",
        application_number="APP-CLEAN-02",
        institution_name="Clean Valley Institute of Pharmacy",
        extracted_params={
            "faculty": [
                {
                    "aadhaar": "7777 8888 9999",
                    "name": "Dr. Neha Patel",
                    "employment_type": "FULL_TIME",
                    "periods": ["2024-2025"],
                },
                {
                    "aadhaar": "4444 5555 6666",  # Same visiting professor
                    "name": "Dr. Sunita Rao",
                    "employment_type": "ADJUNCT",  # Permissible visiting/adjunct!
                    "periods": ["2024-2025"],
                },
            ],
            "fire_noc_number": "NOC/FIRE/DEL/2024/2222",  # Distinct NOC
            "photos": [
                # Distinct photo: 0xffffffff00000000 vs 0x00000000ffffffff (Hamming distance = 64)
                {"phash": "ffffffff00000000", "type": "LAB", "description": "Pharmaceutics Lab"}
            ],
            "seals": [
                # Same seal pHash from the SAME issuing authority is legitimate!
                {"phash": "1234567812345678", "issuing_authority": "Delhi Fire Service"}
            ],
        },
    )

    # College C: Sequential career progression
    # Prof. Amit Verma previously worked here in 2021-2023, then moved to College A in 2024.
    app_c = extractor.extract_from_dossier_data(
        dossier_id="dos-clean-03",
        application_number="APP-CLEAN-03",
        institution_name="Historic Science College",
        extracted_params={
            "faculty": [
                {
                    "aadhaar": fac_a_id,  # Same faculty, but NON-OVERLAPPING past period!
                    "name": "Prof. Amit Verma",
                    "employment_type": "FULL_TIME",
                    "periods": ["2021-2023"],  # Concluded prior to 2024!
                }
            ],
            "fire_noc_number": "NOC/FIRE/PUNE/2023/9999",
            "photos": [
                {"phash": "a5a5a5a55a5a5a5a", "type": "CAMPUS", "description": "Main Gate"}
            ],
            "seals": [
                {"phash": "9999888877776666", "issuing_authority": "Municipal Corporation of Pune"}
            ],
        },
    )

    applications = [
        {"dossier_id": app_a.dossier_id, "institution_name": app_a.institution_name, "entities": app_a.entities},
        {"dossier_id": app_b.dossier_id, "institution_name": app_b.institution_name, "entities": app_b.entities},
        {"dossier_id": app_c.dossier_id, "institution_name": app_c.institution_name, "entities": app_c.entities},
    ]

    all_findings = FraudDetectorEngine.run_all(applications)

    # CRITICAL ASSERTION: Zero false positives on clean control set
    assert len(all_findings) == 0, f"False positives detected on control set: {[f.summary for f in all_findings]}"


# ==============================================================================
# 4. NETWORKX GRAPH BUILDER & CYTOSCAPE EXPORT TESTS
# ==============================================================================

def test_networkx_graph_builder_clusters_and_cytoscape() -> None:
    """Test NetworkX graph building, cluster calculation, and Cytoscape.js format."""
    extractor = EntityExtractor(salt="test-graph-salt")

    # Ingest 2 applications sharing a faculty member
    shared_id = "5555 4444 3333"
    app1 = extractor.extract_from_dossier_data(
        dossier_id="dos-g-01",
        application_number="APP-G-01",
        institution_name="College One",
        extracted_params={
            "faculty": [{"aadhaar": shared_id, "name": "Prof. Shared", "employment_type": "FULL_TIME"}],
            "fire_noc_number": "NOC-101",
        },
    )
    app2 = extractor.extract_from_dossier_data(
        dossier_id="dos-g-02",
        application_number="APP-G-02",
        institution_name="College Two",
        extracted_params={
            "faculty": [{"aadhaar": shared_id, "name": "Prof. Shared", "employment_type": "FULL_TIME"}],
            "fire_noc_number": "NOC-202",
        },
    )

    builder, findings, cyto = fraud_service.build_graph_from_results([app1, app2])

    assert len(findings) == 1  # Ghost faculty
    assert cyto.fraud_detected is True
    assert cyto.total_applications == 2
    assert cyto.total_entities >= 3  # 1 shared faculty, 2 distinct NOCs
    assert len(cyto.elements.nodes) >= 5
    assert len(cyto.elements.edges) >= 4

    # Assert Cytoscape elements structure
    app_nodes = [n for n in cyto.elements.nodes if n.data.node_type == "application"]
    assert len(app_nodes) == 2
    for an in app_nodes:
        assert an.data.cluster_id > 0
        assert an.data.severity == "FLAGGED_TAMPER"

    # Both applications must be in the same connected cluster because they share the faculty entity
    assert app_nodes[0].data.cluster_id == app_nodes[1].data.cluster_id

    # Check cluster summary
    assert len(cyto.clusters) >= 1
    cluster_1 = cyto.clusters[0]
    assert cluster_1.max_severity == "FLAGGED_TAMPER"
    assert "dos-g-01" in cluster_1.involved_application_ids
    assert "dos-g-02" in cluster_1.involved_application_ids


# ==============================================================================
# 5. FASTAPI INTEGRATION & INCREMENTAL DB INDEXING
# ==============================================================================

@pytest.mark.asyncio
async def test_api_fraud_endpoints_and_incremental_indexing() -> None:
    """Test FastAPI fraud endpoints and incremental updates via database."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create two dossiers via API
        shared_fac = "7711 8822 9933"
        d1_payload = {
            "institution_name": "API Apex Tech",
            "application_number": f"APP-API-01-{uuid.uuid4().hex[:4]}",
            "program": "Engineering & Technology",
        }
        r1 = await ac.post("/api/dossiers", json=d1_payload)
        assert r1.status_code == 200
        d1_id = r1.json()["dossier_id"]

        d2_payload = {
            "institution_name": "API Beacon Tech",
            "application_number": f"APP-API-02-{uuid.uuid4().hex[:4]}",
            "program": "Engineering & Technology",
        }
        r2 = await ac.post("/api/dossiers", json=d2_payload)
        assert r2.status_code == 200
        d2_id = r2.json()["dossier_id"]

        # 2. Plant params into database for both dossiers
        from nirikshan.db.models import DossierModel
        from nirikshan.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db_session:
            dm1 = await db_session.get(DossierModel, d1_id)
            assert dm1 is not None
            dm1.set_extracted_params({
                "faculty": [{"aadhaar": shared_fac, "name": "Dr. Dual", "employment_type": "FULL_TIME"}],
                "fire_noc_number": "NOC-API-SHARED-99",
            })
            dm2 = await db_session.get(DossierModel, d2_id)
            assert dm2 is not None
            dm2.set_extracted_params({
                "faculty": [{"aadhaar": shared_fac, "name": "Dr. Dual", "employment_type": "FULL_TIME"}],
                "fire_noc_number": "NOC-API-SHARED-99",
            })
            await db_session.commit()

        # 3. Test incremental indexing endpoint for both dossiers
        idx1_res = await ac.post(f"/api/fraud/index/{d1_id}")
        assert idx1_res.status_code == 200
        idx1_data = idx1_res.json()
        assert idx1_data["dossier_id"] == d1_id
        assert len(idx1_data["entities"]) >= 2

        idx2_res = await ac.post(f"/api/fraud/index/{d2_id}")
        assert idx2_res.status_code == 200
        idx2_data = idx2_res.json()
        assert idx2_data["dossier_id"] == d2_id

        # 4. Test fraud graph endpoint returning Cytoscape.js format
        graph_res = await ac.get("/api/fraud/graph")
        assert graph_res.status_code == 200
        graph_data = graph_res.json()
        assert "elements" in graph_data
        assert "nodes" in graph_data["elements"]
        assert "edges" in graph_data["elements"]
        assert "clusters" in graph_data
        assert "findings" in graph_data

        assert graph_data["fraud_detected"] is True
        assert len(graph_data["findings"]) >= 2  # Both Ghost Faculty and Certificate Sharing

        # 5. Test scan and findings endpoints
        scan_res = await ac.post("/api/fraud/scan")
        assert scan_res.status_code == 200
        findings_data = scan_res.json()
        assert len(findings_data) >= 2

        findings_res = await ac.get("/api/fraud/findings")
        assert findings_res.status_code == 200
        assert len(findings_res.json()) >= 2
