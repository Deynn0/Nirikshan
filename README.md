# Nirikshan (निरीक्षण)

> **Offline-first, explainable regulatory scrutiny platform for institutional approval under the AICTE Approval Process Handbook (APH).**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()
[![Air-Gapped](https://img.shields.io/badge/Security-100%25%20Air--Gapped-success.svg)]()

---

## 🏛️ The Nirikshan Constitution

All components, features, and pull requests in Nirikshan are strictly audited against the **Nirikshan Constitution**:

1. **Trust Ladder Hierarchy & Strict PASS Trust-Gating**: Evidence follows a strict ordinal precedence:
   $$\text{CRYPTOGRAPHIC (6)} > \text{ISSUER (5)} > \text{RECORD (4)} > \text{RULE (3)} > \text{STRUCTURAL\_FORENSIC (2)} > \text{MODEL (1)} > \text{UNVERIFIED\_CLAIM (0)}$$
   - Self-attestation always ranks as `UNVERIFIED_CLAIM`.
   - Machine learning (OCR, vision models, LLMs) is strictly `MODEL` (advisory only).
   - **Constitutional Invariant**: No Model-level or self-attested item can ever produce a verified `PASS`. Rules with only model or claim evidence automatically evaluate to `UNVERIFIED` and downgrade findings to `MANUAL_REVIEW_REQUIRED`.
2. **Mandatory Sandboxed Ingestion**: All untrusted applicant PDFs and image artifacts are stored in an encrypted quarantine (`AES-GCM-256`) and parsed exclusively inside an isolated worker subprocess with strict OS resource ceilings (`RLIMIT_AS`, `RLIMIT_CPU`, timeout watchdog).
3. **100% Offline & Air-Gapped Operation**: Zero outbound network requests at runtime. All socket connections to non-loopback addresses are blocked at the kernel/socket layer via `_install_airgap_guard()`.
4. **Full Explainability & Citations**: Every finding includes an authoritative handbook citation (`Clause`, `Page`, `Edition`), itemized evidence items with computed trust levels, and spatial bounding boxes (`[page, x, y, width, height]`).
5. **Cryptographic Audit Ledger & Deterministic Audit Replay**: Every evaluation step is committed to an append-only, SHA-256 hash-chained ledger. Complete historical evaluations can be replayed bit-for-bit to verify deterministic consistency.

For full architectural details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📁 Repository Structure

```text
nirikshan/
├── backend/
│   ├── nirikshan/
│   │   ├── advisory/         # Advisory ML: YOLOX-M vision, Ask-Why LLM, entity extraction
│   │   ├── api/              # FastAPI endpoints (dossiers, scrutiny, documents, audit)
│   │   ├── core/             # Configuration, database, air-gap guard, safe evaluation
│   │   ├── engine/           # Audit log service, SHA-256 hash-chaining, replay
│   │   ├── fraud/            # Cross-application NetworkX fraud graph & ring detection
│   │   ├── ingest/           # PDF text extractor, pikepdf metadata, font analysis
│   │   ├── rules/            # AST-safe deterministic rules engine & trust-gating
│   │   ├── sandbox/          # Sandboxed subprocess worker & quarantine storage
│   │   └── schemas/          # Pydantic v2 domain models (Finding, Dossier, Evidence)
│   ├── rulesets/             # Declarative AICTE APH regulatory rules (YAML)
│   ├── scripts/              # Evaluation benchmarks and fixture generation
│   ├── tests/                # Integration and unit test suite
│   └── var/                  # Local SQLite database & quarantine spool
├── docs/                     # Architectural specifications and regulatory citations
├── frontend/
│   ├── src/
│   │   ├── api/              # Typed backend REST client
│   │   ├── components/       # UI components (DocumentViewer, TrustLadderBadge, Graph)
│   │   ├── pages/            # Officer Scrutiny Console, Audit Ledger, Fraud Network
│   │   └── test/             # Vitest setup & unit test suites
│   ├── package.json
│   └── vite.config.ts
├── Makefile                  # Linux/macOS build automation
├── make.bat                  # Windows batch runner
└── make.ps1                  # Windows PowerShell script runner
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python**: Version 3.11+
- **Node.js**: Version 18+ (Node 20+ recommended) and `npm`
- **Operating System**: Windows 10/11, Ubuntu 22.04+, or macOS Sonoma+

---

### 1. Backend Setup

#### On Windows (PowerShell):
```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -e .
```

#### On Linux / macOS:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Verify frontend build
npm run build
```

---

## ⚡ Running Development Servers

### Option A: Using Helper Scripts

#### Windows PowerShell:
```powershell
# Start backend server (http://127.0.0.1:8000)
.\make.ps1 dev
```

#### Linux / macOS:
```bash
# Start backend server
make dev
```

### Option B: Running Manually

1. **Backend Server**:
   ```bash
   cd backend
   # Windows:
   .\.venv\Scripts\uvicorn nirikshan.main:app --reload --port 8000 --host 127.0.0.1
   # Linux/macOS:
   ./.venv/bin/uvicorn nirikshan.main:app --reload --port 8000 --host 127.0.0.1
   ```
   API docs available at: `http://127.0.0.1:8000/docs`

2. **Frontend Dev Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   Officer Scrutiny Console available at: `http://localhost:5173`

---

## 🧪 Testing & Validation

### 1. Nirikshan Constitution Integration Test
Verify all 5 constitutional pillars in a single end-to-end integration test:
```powershell
# Windows
.\backend\.venv\Scripts\pytest backend\tests\test_constitution_integration.py -v

# Linux/macOS
backend/.venv/bin/pytest backend/tests/test_constitution_integration.py -v
```

### 2. Full Backend Test Suite
```powershell
# Windows
.\make.ps1 test

# Linux/macOS
make test
```
*Current status: 133/133 tests passing.*

### 3. Frontend Unit Tests
```bash
cd frontend
npm test
```
*Current status: 10/10 tests passing.*

### 4. Synthetic Evaluation Benchmark
Evaluates the rules engine against 24 synthetic institutional fixtures across 4 major institutional categories (Engineering, Pharmacy, Management, Architecture) with strict zero-false-alarm thresholds:
```powershell
# Windows
.\make.ps1 eval

# Linux/macOS
make eval
```
*Benchmark status: 24/24 fixtures passing, Macro F1 = 1.000.*

### 5. Linting & Type Checking
```powershell
# Windows
.\make.ps1 lint

# Linux/macOS
make lint
```
Runs `ruff check .` and `mypy nirikshan` in strict mode.

---

## 🛡️ Security & Air-Gap Verification

To verify that the application refuses any outbound connection to external servers:
```python
import socket

# When NIRIKSHAN_ALLOW_EXTERNAL_NETWORK=False (default)
# Any socket attempt to external IPs (e.g., 8.8.8.8, 1.1.1.1) throws AirGapViolationError
s = socket.socket()
s.connect(("8.8.8.8", 53))  # -> AirGapViolationError: Air-gap violation: outbound connection blocked
```

---

## 📊 Officer Scrutiny Console Workflow

1. **Dossier Inspection**: Scrutiny officers view applications with visual trust-ladder indicators for every document.
2. **Side-by-Side Document Viewer**: Click any finding to instantly jump to the exact bounding box in the source PDF canvas.
3. **Revision Time Machine**: Inspect incremental PDF revision history to uncover retroactively altered text or replaced stamps.
4. **Cross-Application Integrity Graph**: Discover hidden fraud syndicates pledging duplicate land, bank guarantees, or faculty across states.
5. **Cryptographic Audit Ledger & Replay**: Verify the SHA-256 hash chain and replay historical evaluations with one click.
