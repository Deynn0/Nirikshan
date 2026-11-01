# Cross-Application Fraud Graph: Architecture & Detection Guidelines

## 1. Overview & Objective

The **Cross-Application Fraud Graph** is Nirikshan's multi-institution scrutiny subsystem designed to detect syndicated fraud, document recycling, and regulatory impersonation across independent application dossiers under the **AICTE Approval Process Handbook (APH) 2024–2027**.

While single-dossier verification validates internal consistency and cryptographic tamper evidence within an isolated institution, sophisticated bad actors frequently recycle assets across multiple applications:
- Registering the same senior faculty member ("Ghost Faculty") across multiple institutions to meet mandatory Teacher-Student Ratios (SFR).
- Sharing the same Fire Safety NOC or Land Title Deed between different institutions.
- Submitting identical laboratory and campus infrastructure photos for physically separate campuses.
- Digitally superimposing official statutory seals across disparate municipal and state authorities.

---

## 2. Graph Data Model & Incremental Indexing

### Bipartite Multi-Modal NetworkX Graph
The graph $G = (V, E)$ is modeled with two primary node classes and directional/undirected semantic edges:

1. **Application Nodes ($V_{\text{app}}$)**:
   - Identifier: `app:<dossier_id>`
   - Attributes: `institution_name`, `application_number`, `program`, `risk_score`, `cluster_id`, `severity`.
2. **Entity Nodes ($V_{\text{entity}}$)**:
   - Identifier: `ent:<entity_type>:<entity_value>`
   - Types:
     - `FACULTY`: Salted HMAC-SHA256 hash of Aadhaar or PAN.
     - `CERTIFICATE`: Normalized certificate number (e.g., Fire NOC, Building Completion).
     - `FILE_HASH`: SHA-256 cryptographic hash of document binaries.
     - `PHOTO_PHASH`: Perceptual hash (pHash 64-bit) of lab and campus photos.
     - `SEAL_PHASH`: Perceptual hash of detected physical rubber/digital seals.
     - `LAND_REG`: Sub-Registrar registration deed / survey / khasra numbers.
     - `DECLARED_ADDRESS`: Normalized declared institutional address.
3. **Edges ($E$)**:
   - `uses`: Links an Application node to an Entity node (`app -> uses -> entity`).
   - `perceptual_match`: Links two visual entities (`PHOTO_PHASH` or `SEAL_PHASH`) whose Hamming distance is within the tuned threshold ($\text{dist} \le \tau$).

### Incremental State Persistence
To allow streaming ingestion and avoid expensive $O(N^2)$ global re-indexing:
- Extracted entities are stored in `entity_index` (keyed by deterministic `entity_id`).
- Dossier-to-entity relations are stored in `application_entity_edges` with foreign key cascades.
- When an application dossier is updated or re-verified, its edges are refreshed atomically without altering other institutions in the index.

---

## 3. Cryptographic PII Protection (Aadhaar & PAN)

> [!IMPORTANT]
> **Strict Non-Negotiable Privacy Constraint:**
> Plaintext Aadhaar (12-digit UID) and Income Tax PAN (10-character alphanumeric) are **NEVER** stored in the database, logged to disk, or serialized in API graph responses.

### Salting Architecture
- When faculty credentials are read, they are immediately transformed via:
  $$\text{Hash} = \text{HMAC-SHA256}(\text{Salt}, \text{Normalize}(\text{RawID}))$$
- Where $\text{Normalize}(\text{RawID})$ strips all whitespace, hyphens, and punctuation and converts characters to uppercase.
- The system salt is loaded from `NIRIKSHAN_FRAUD_SALT` (configured via environment variable or air-gapped security vault).
- This produces a deterministic 64-character hexadecimal digest. Identical faculty IDs submitted across two separate institutions yield the exact same digest, enabling cross-institution intersection while rendering rainbow table and brute-force reconstruction computationally infeasible.
- Visual labels in Cytoscape.js only display masked identifiers (e.g. `XXXX-XXXX-1234` or `XXXXXX123F`).

---

## 4. Fraud Detectors & Statutory Handbook Citations

| Detector | AICTE APH Citation | Detection Logic | Finding Severity |
| :--- | :--- | :--- | :--- |
| **Ghost Faculty** | Clause 4.3 & Appendix 7 (*Faculty Norms*) | Same faculty salted hash declared as **Full-Time** across $\ge 2$ institutions with overlapping academic periods. | `FLAGGED_TAMPER` |
| **Certificate Sharing** | Clause 5.1 & Clause 2.4 (*Essential Infrastructure*) | Same Fire NOC or Land Registration number shared across unrelated institutions. | `FLAGGED_TAMPER` |
| **Photo Reuse** | Clause 6.2 (*Physical Verification*) | Lab or campus photos submitted by separate applicants with pHash Hamming distance $\le \tau_{\text{photo}}$. | `FLAGGED_TAMPER` |
| **Seal Reuse** | Clause 1.4 & Appendix 1 (*Statutory Approvals*) | Same seal pHash ($\text{dist} \le \tau_{\text{seal}}$) claiming attribution to **different** issuing authorities. | `FLAGGED_TAMPER` |

---

## 5. False-Positive Considerations & Threshold Tuning

Detection of cross-application anomalies in regulatory audits carries severe administrative and legal consequences (e.g., withdrawal of AICTE approval). Consequently, thresholds and detector logic must distinguish intentional fraud from legitimate operational overlap.

### 5.1. Ghost Faculty
- **False-Positive Risk 1: Visiting & Adjunct Faculty**
  - *Context:* AICTE regulations explicitly permit institutions to engage Adjunct and Visiting Faculty up to 20% of their total faculty cadre. A professor may legitimately teach guest modules at College A while serving as visiting faculty at College B.
  - *Mitigation:* The detector **only** triggers when multiple institutions declare the faculty member under a `FULL_TIME` or permanent appointment contract.
- **False-Positive Risk 2: Sequential Career Progression**
  - *Context:* A faculty member who resigned from Institution A in June 2023 and joined Institution B in July 2023 is merely progressing in their career.
  - *Mitigation:* The detector performs temporal intersection (`check_periods_overlap`). If academic sessions are disjoint (e.g. `2021-2023` vs `2023-2025`), zero finding is flagged.
- **False-Positive Risk 3: Single-Institution Duplicate Entry**
  - *Context:* Administrative data entry errors in which a college uploads the same professor in both the Department of Computer Science and Department of Information Technology.
  - *Mitigation:* Grouping checks ensure uniqueness across distinct `dossier_id`s before evaluation.

### 5.2. Certificate Sharing
- **False-Positive Risk: Multi-Institution Integrated Campuses**
  - *Context:* A single registered Educational Trust running an Engineering College, a Pharmacy College, and an Architecture School on a contiguous, legally shared educational campus under AICTE Clause 2.15 ("Integrated Campus Norms"). Such institutions frequently share a single master municipal Fire Safety NOC.
  - *Mitigation:* When `fraud_allow_shared_parent_trust` is enabled, institutions sharing the identical parent trust and declaring common integrated infrastructure are treated as sister institutions and exempt from fraud flagging.

### 5.3. Photo Reuse
- **False-Positive Risk 1: Standardized OEM Equipment**
  - *Context:* Technical colleges often procure standard educational equipment (e.g. universal testing machines, lathe machines, brand-name electronics trainer kits) from the same educational vendor, which may include stock equipment catalog photographs in equipment lists.
  - *Mitigation:* The pHash Hamming threshold $\tau_{\text{photo}}$ is tuned to **6 bits** (on 64-bit DCT perceptual hash). Distinct physical rooms with different angles, wall colors, lighting, and student setups exhibit distances $> 15\text{ bits}$. Only direct digital duplicates, resized copies, or minor crops trigger the flag.
- **False-Positive Risk 2: Low-Resolution Scans**
  - *Context:* Highly degraded scans can lose high-frequency features, artificially compressing distances.
  - *Mitigation:* Pre-filtering verifies minimal image entropy before perceptual hashing.

### 5.4. Seal Reuse
- **False-Positive Risk: Same Issuing Authority Across Dossiers**
  - *Context:* The Delhi Fire Service issues fire NOCs to multiple engineering colleges across New Delhi. All genuine NOCs naturally bear the official circular seal of the Delhi Fire Service.
  - *Mitigation:* The detector **requires normalized authority disparity**:
    $$\text{Normalize}(\text{Auth}_A) \ne \text{Normalize}(\text{Auth}_B)$$
    Legitimate seals from the *same* authority are expected to match and are never flagged. The detector strictly catches instances where a single stamp graphic has been copy-pasted across different departments (e.g. Municipal Corporation stamp appearing on a Police or Fire NOC).

---

## 6. Configurable Thresholds

The parameters are exposed in `backend/nirikshan/config.py` and can be overridden via system environment variables:

```ini
# HMAC-SHA256 Salt for Aadhaar and PAN masking
NIRIKSHAN_FRAUD_SALT="airgapped-salt-secret-aicte-2024"

# Maximum Hamming distance (0-64) to qualify as recycled laboratory photo
NIRIKSHAN_FRAUD_PHOTO_HAMMING_THRESHOLD=6

# Maximum Hamming distance to qualify as identical physical seal clone
NIRIKSHAN_FRAUD_SEAL_HAMMING_THRESHOLD=5

# Address similarity token ratio for land location matching
NIRIKSHAN_FRAUD_ADDRESS_SIMILARITY_THRESHOLD=0.85

# Treat sister colleges under identical registered trust as exempt from certificate sharing
NIRIKSHAN_FRAUD_ALLOW_SHARED_PARENT_TRUST=True
```

---

## 7. Cytoscape.js Format & Visualization Schema

The API endpoint `GET /api/fraud/graph` returns the graph structure formatted for Cytoscape.js visualization consoles:

```json
{
  "elements": {
    "nodes": [
      {
        "data": {
          "id": "app:dos-101",
          "label": "Apex Institute of Technology",
          "node_type": "application",
          "cluster_id": 1,
          "severity": "FLAGGED_TAMPER",
          "institution_name": "Apex Institute of Technology",
          "risk_score": 95.0
        }
      },
      {
        "data": {
          "id": "ent:FACULTY:a3f9...",
          "label": "Faculty (XXXX-XXXX-4321)",
          "node_type": "entity",
          "entity_type": "FACULTY",
          "cluster_id": 1,
          "severity": "FLAGGED_TAMPER"
        }
      }
    ],
    "edges": [
      {
        "data": {
          "id": "edge:dos-101:FACULTY:a3f9...",
          "source": "app:dos-101",
          "target": "ent:FACULTY:a3f9...",
          "relation": "uses",
          "cluster_id": 1,
          "severity": "FLAGGED_TAMPER"
        }
      }
    ]
  },
  "clusters": [
    {
      "cluster_id": 1,
      "size": 6,
      "max_severity": "FLAGGED_TAMPER",
      "fraud_types": ["Ghost Faculty: Simultaneous Full-Time Appointment"],
      "involved_application_ids": ["dos-101", "dos-102"],
      "involved_institutions": ["Apex Institute of Technology", "Beacon College of Engineering"]
    }
  ],
  "findings": [...]
}
```

This representation enables instant visualization of syndicated syndicates in inspection consoles, highlighting high-risk clusters in red while displaying compliant singletons in green.
